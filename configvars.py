vars = [
    ("BOOST_INC_DIR", None,
        "The include directory for all of Boost C++"),
    ("BOOST_LIB_DIR", None,
        "The library directory for all of Boost C++"),
    ("BOOST_PYTHON_LIBNAME", "boost_python-gcc41-mt",
        "The name of the Boost Python library binary (without lib and .so)"),
    # -------------------------------------------------------------------------
    ("BOOST_BINDINGS_INC_DIR", None,
        "The include directory for the Boost bindings library"),
    ("BOOST_MATH_TOOLKIT_INC_DIR", None,
        "The include directory for the Boost math toolkit"),
    # -------------------------------------------------------------------------
    ("HAVE_MPI", False,
        "Whether to build with support for MPI"),
    ("MPICC", "mpicc",
        "Path to MPI C compiler"),
    ("MPICXX", None,
        "Path to MPI C++ compiler (defaults to same as MPICC)"),
    ("BOOST_MPI_LIBNAME", "boost_mpi-gcc42-mt",
        "Path to MPI C++ compiler (defaults to same as MPICC)"),
    # -------------------------------------------------------------------------
    ("CXXFLAGS", "-Wno-sign-compare",
        "Any extra C++ compiler options to include"),
    ]

subst_files = ["Makefile", "siteconf.py"]
