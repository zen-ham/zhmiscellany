from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "fast_array_diff",
        ["fast_array_diff.cpp"],
        extra_compile_args=["-std=c++17"],
    ),
]

setup(
    name="fast_array_diff",
    version="0.2",
    author="@z_h_ on Discord",
    author_email="not_giving_this@example.com",
    description="I am speed",
    long_description="",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.0",
)
