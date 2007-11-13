from __future__ import division
import pylinear.array as num
import pylinear.computation as comp
import pylinear.operator as op
import cProfile as profile




def add_gauss_particles(nparticles, cloud, discr, charge, mass, 
        mean_x, mean_p, sigma_x, sigma_p):
    from random import gauss
    from pyrticle.cloud import v_from_p

    cloud.add_particles(
            positions=[
                num.array([gauss(m, s) for m, s in zip(mean_x, sigma_x)]) 
                for i in range(nparticles)
                ],
            velocities=[v_from_p(
                num.array([gauss(m, s) for m, s in zip(mean_p, sigma_p)]),
                mass, cloud.units.VACUUM_LIGHT_SPEED) 
                for i in range(nparticles)
                ],
            charges=charge, masses=mass)



def main():
    from hedge.element import TriangularElement
    from hedge.timestep import RK4TimeStepper
    from hedge.mesh import \
            make_square_mesh
    from hedge.discretization import \
            Discretization, \
            pair_with_boundary
    from hedge.visualization import VtkVisualizer, SiloVisualizer
    from hedge.tools import dot
    from math import sqrt, pi
    from pytools.arithmetic_container import \
            ArithmeticList, join_fields
    from hedge.operators import TEMaxwellOperator, DivergenceOperator
    from pyrticle.cloud import ParticleCloud
    from random import seed
    #seed(0)

    from pyrticle.units import SI
    units = SI()

    # discretization setup ----------------------------------------------------
    #full_mesh = make_cylinder_mesh(radius=25*units.MM, height=100*units.MM, periodic=True,
            #max_volume=100*units.MM**3, radial_subdivisions=10)
    #full_mesh = make_box_mesh([1,1,2], max_volume=0.01)
    full_mesh = make_square_mesh(max_area=0.1)

    from hedge.parallel import guess_parallelization_context

    pcon = guess_parallelization_context()

    if pcon.is_head_rank:
        mesh = pcon.distribute_mesh(full_mesh)
    else:
        mesh = pcon.receive_mesh()

    discr = pcon.make_discretization(mesh, TriangularElement(5))
    vis = SiloVisualizer(discr)
    #vis = VtkVisualizer(discr, "pic")

    max_op = TEMaxwellOperator(discr, 
            epsilon=units.EPSILON0, 
            mu=units.MU0, 
            upwind_alpha=1)
    div_op = DivergenceOperator(discr)

    dt = discr.dt_factor(max_op.c) / 2
    final_time = 1*units.M/max_op.c
    nsteps = int(final_time/dt)+1
    dt = final_time/nsteps

    print "#elements=%d, dt=%s, #steps=%d" % (
            len(discr.mesh.elements), dt, nsteps)

    def l2_norm(field):
        return sqrt(dot(field, discr.mass_operator*field))
    def l2_error(field, true):
        return l2_norm(field-true)/l2_norm(true)

    # particles setup ---------------------------------------------------------
    nparticles = 10

    cloud = ParticleCloud(max_op, units, dimensions_pos=2, dimensions_velocity=2,
            verbose_vis=True)

    cloud_charge = 1e-9 * units.C
    particle_charge = cloud_charge/nparticles
    electrons_per_particle = cloud_charge/nparticles/units.EL_CHARGE
    print "e-/particle = ", electrons_per_particle 

    avg_x_vel = 0.8*units.VACUUM_LIGHT_SPEED
    mean_v = num.array([avg_x_vel, 0])
    mean_beta = mean_v/units.VACUUM_LIGHT_SPEED
    gamma = units.gamma(mean_v)
    pmass = electrons_per_particle*units.EL_MASS
    mean_p = gamma*pmass*mean_v

    add_gauss_particles(nparticles, cloud, discr, 
            charge=units.EL_CHARGE, 
            mass=pmass,
            mean_x=num.zeros((2,)),
            mean_p=mean_p,
            sigma_x=0.3*num.ones((2,)),
            sigma_p=units.gamma(mean_v)*pmass*num.ones((2,))*avg_x_vel*0.1,
            )

    # intial condition --------------------------------------------------------
    def compute_initial_condition():
        from hedge.operators import WeakPoissonOperator
        from hedge.mesh import TAG_ALL, TAG_NONE
        from hedge.data import ConstantGivenFunction, GivenVolumeInterpolant
        from hedge.tools import cross

        # see doc/notes.tm for derivation of IC

        diff_tensor = num.identity(discr.dimensions)
        diff_tensor[0,0] = 1/gamma**2

        poisson_op = WeakPoissonOperator(discr, 
                diffusion_tensor=ConstantGivenFunction(diff_tensor),
                dirichlet_tag=TAG_ALL,
                neumann_tag=TAG_NONE,
                )

        rho = cloud.reconstruct_rho() 

        from hedge.tools import parallel_cg
        phi = -parallel_cg(pcon, -poisson_op, 
                poisson_op.prepare_rhs(
                    GivenVolumeInterpolant(discr, rho/max_op.epsilon)), 
                debug=True, tol=1e-10)

        etilde = ArithmeticList([1/gamma,1])*poisson_op.grad(phi)

        eprime = ArithmeticList([1, gamma])*etilde

        hprime = (1/max_op.mu)*gamma/max_op.c * max_op.e_cross(mean_beta, etilde)

        rhoprime = gamma*rho
        divDprime_ldg = max_op.epsilon*poisson_op.div(eprime)
        divDprime_ldg2 = max_op.epsilon*poisson_op.div(eprime, gamma*phi)
        divDprime_ldg3 = max_op.epsilon*gamma*\
                (discr.inverse_mass_operator*poisson_op.op(phi))
        divDprime_central = max_op.epsilon*div_op(eprime)

        print "l2 div error ldg: %g" % \
                l2_error(divDprime_ldg, rhoprime)
        print "l2 div error central: %g" % \
                l2_error(divDprime_central, rhoprime)
        print "l2 div error ldg with phi: %g" % \
                l2_error(divDprime_ldg2, rhoprime)
        print "l2 div error ldg with phi 3: %g" % \
                l2_error(divDprime_ldg3, rhoprime)

        if True:
            visf = vis.make_file("ic")
            vis.add_data(visf,
                    [ 
                        ("rho", rhoprime), 
                        ("divDldg", divDprime_ldg),
                        ("divDldg2", divDprime_ldg2),
                        ("divDldg3", divDprime_ldg3),
                        ("divDcentral", divDprime_central),
                        ("phi", phi),
                        ("e", eprime), 
                        ("h", hprime), 
                        ],
                    scale_factor=1e30
                    )
            cloud.add_to_vis(vis, visf)
            visf.close()

        return join_fields(eprime, hprime, [cloud])

    fields = compute_initial_condition()

    # timestepping ------------------------------------------------------------

    def rhs(t, y):
        e, h = max_op.split_fields(y)

        velocities = cloud.velocities()
        maxwell_rhs = max_op.rhs(t, y[0:6])
        rho, j = cloud.reconstruct_densities(velocities)
        cloud_rhs = cloud.rhs(t, e, h, velocities)

        rhs_e = maxwell_rhs[:3]
        rhs_h = maxwell_rhs[3:6]
        return join_fields(
                rhs_e - 1/max_op.epsilon*j,
                rhs_h,
                ).plus([cloud_rhs])

    stepper = RK4TimeStepper()
    from time import time
    last_tstep = time()
    t = 0

    for step in xrange(nsteps):
        if False:
            myfields = [fields]
            fields = profile.runctx("myfields[0] = stepper(fields, t, dt, rhs)", 
                    globals(), locals(), "pic-%04d.prof" % step)
            fields = myfields[0]
        else:
            fields = stepper(fields, t, dt, rhs)

        cloud.upkeep()

        print "timestep %d, t=%g l2[e]=%g l2[h]=%g secs=%f particles=%d" % (
                step, t, l2_norm(fields[0:3]), l2_norm(fields[3:6]),
                time()-last_tstep, len(cloud))
        if False:
            print "searches: same=%d, normal=%d, vertex=%d, global=%d, periodic=%d" % (
                    cloud.same_searches.pop(),
                    cloud.normal_searches.pop(),
                    cloud.vertex_searches.pop(),
                    cloud.global_searches.pop(),
                    cloud.periodic_hits.pop(),
                    )
            print "shape-adds: neighbor=%d vertex=%d" % (
                    cloud.neighbor_shape_adds.pop(),
                    cloud.vertex_shape_adds.pop(),
                    )

        last_tstep = time()

        if True:
            visf = vis.make_file("pic-%04d" % step)

            mesh_scalars, mesh_vectors = \
                    cloud.add_to_vis(vis, visf, time=t, step=step)
            vis.add_data(visf, [
                        ("divD", max_op.epsilon*div_op(fields[0:3])),
                        ("e", fields[0:3]), 
                        ("h", fields[3:6]), 
                        ] + mesh_scalars + mesh_vectors,
                    time=t, step=step)
            visf.close()

        t += dt

    vis.close()




if __name__ == "__main__":
    #profile.run("main()", "pic.prof")
    main()