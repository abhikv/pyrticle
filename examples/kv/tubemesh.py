from __future__ import division




def make_cylinder_with_fine_core(r, inner_r, min_z, max_z, 
        max_volume_inner=1e-4, max_volume_outer=5e-2,
        radial_subdiv=20):

        from meshpy.tet import MeshInfo, build, \
                generate_surface_of_revolution, \
                EXT_CLOSED_IN_RZ, EXT_OPEN, EXT_CLOSE_IN_Z

        MINUS_Z_MARKER = 1
        PLUS_Z_MARKER = 2

        inner_points, inner_facets, inner_markers, inner_holes = \
                generate_surface_of_revolution(
                        [
                            (inner_r, min_z), 
                            (inner_r, max_z),
                            ],
                        minus_z_closure_marker=MINUS_Z_MARKER,
                        plus_z_closure_marker=PLUS_Z_MARKER,
                        radial_subdiv=radial_subdiv,
                        closure=EXT_CLOSE_IN_Z)

        inner_point_indices = range(len(inner_points))

        outer_points, outer_facets, outer_markers, outer_holes = \
                generate_surface_of_revolution(
                        [ (inner_r,min_z), 
                            (r, min_z), 
                            (r, max_z),
                            (inner_r, max_z)
                            ], 
                        ring_markers=[MINUS_Z_MARKER, 0, PLUS_Z_MARKER],
                        point_idx_offset=len(inner_points),
                        closure=EXT_OPEN,
                        radial_subdiv=radial_subdiv,
                        ring_point_indices=[
                            inner_point_indices[:radial_subdiv],
                            None,
                            None,
                            inner_point_indices[radial_subdiv:],
                            ]
                        )

        mesh_info = MeshInfo()
        mesh_info.set_points(inner_points + outer_points)
        mesh_info.set_facets_ex(
                inner_facets + outer_facets,
                inner_markers + outer_markers,
                inner_holes + outer_holes)

        # set regional max. volume
        mesh_info.regions.resize(2)
        mesh_info.regions[0] = [0, 0, (max_z+min_z)/2, 0, 
                max_volume_inner]
        mesh_info.regions[1] = [inner_r+(r-inner_r)/2, 0, (max_z+min_z)/2, 0, 
                max_volume_outer]

        # add periodicity
        mesh_info.pbc_groups.resize(1)
        pbcg = mesh_info.pbc_groups[0]

        pbcg.facet_marker_1 = MINUS_Z_MARKER
        pbcg.facet_marker_2 = PLUS_Z_MARKER

        pbcg.set_transform(translation=[0,0,max_z-min_z])

        mesh = build(mesh_info, verbose=True, volume_constraints=True)
        #print "%d elements" % len(mesh.elements)
        #mesh.write_vtk("gun.vtk")

        from hedge.mesh import ConformalMesh

        fvi2fm = mesh.face_vertex_indices_to_face_marker
            
        def zper_boundary_tagger(fvi, el, fn):
            face_marker = fvi2fm[frozenset(fvi)]
            if face_marker == MINUS_Z_MARKER:
                return ["minus_z"]
            elif face_marker == PLUS_Z_MARKER:
                return ["plus_z"]
            else:
                return ["shell"]

        return ConformalMesh(mesh.points, mesh.elements,
                zper_boundary_tagger,
                periodicity=[None, None, ("minus_z", "plus_z")])

