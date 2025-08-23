from setuptools import setup, find_packages

setup(
    name="goal-tracker",
    version="1.0.0",
    description="A GTK3-based application for tracking progress towards goals",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "PyGObject>=3.40",
    ],
    entry_points={
        'gui_scripts': [
            'goal-tracker=goal_tracker:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications :: GTK",
    ],
    python_requires=">=3.6",
)