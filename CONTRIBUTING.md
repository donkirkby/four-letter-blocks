# Contributing to the Four-Letter Blocks Project
If you like this project and want to make it better, please help out. It could
be as simple as sending [@donkirkby] a nice note on Twitter, you could report a
bug, or pitch in with some development work. Check if there are some issues
labeled as [good first issues] or [help wanted].

[@donkirkby]: https://twitter.com/donkirkby
[good first issues]: https://github.com/donkirkby/four-letter-blocks/labels/good%20first%20issue
[help wanted]: https://github.com/donkirkby/four-letter-blocks/labels/help%20wanted

## Bug Reports and Enhancement Requests
Please create issue descriptions [on GitHub][issues]. Be as specific as possible.
Which version are you using? What did you do? What did you expect to happen? Are
you planning to submit your own fix in a pull request? Please include a puzzle
definition text file if that helps recreate the problem.

[issues]: https://github.com/donkirkby/four-letter-blocks/issues?state=open

## Building a Release
The nice thing about using the [PySide GUI] is that users can install
Four-Letter Blocks with pip. Releasing a new version means publishing it on the
[Python package index] where pip can find it. The details are at
[packaging.python.org], but the main steps are:

1. Pull to make sure you have the latest source code.
2. Update the version number in `four_letter_blocks/__init__.py` and
   development status in `setup.py`.
3. Activate the project's Python virtual environment.

        pipenv shell

4. Temporarily install the build tools using pip, not pipenv.

        python -m pip install --upgrade pip setuptools wheel twine

5. Build the release files.

        python setup.py sdist bdist_wheel

6. Upload the release to PyPI. You'll need a user name and password.

        ls dist/*
        twine upload dist/*

7. Check that the new version is on the [package page], and try installing it.

        pip install --no-cache four-letter-blocks

8. Remove the uploaded files, deactivate the virtual environment, and recreate
   it.

        rm dist/*
        exit
        pipenv clean

9. Commit the version number changes, push, and create a release on GitHub.

[packaging.python.org]: https://packaging.python.org/tutorials/packaging-projects/
[package page]: https://pypi.org/project/four-letter-blocks/
[PySide GUI]: https://wiki.qt.io/Qt_for_Python
[Python package index]: https://pypi.org/

## PySide6 Tools
To edit the GUI, do the following:

1. Download and install [Qt Creator].
2. Run Qt Creator, and open the `.ui` file for the screen you want to change.
3. Read the [Qt Designer documentation], and make the changes you want.
4. Compile the `.ui` file into a Python source file with a command like this:

        pyside6-uic -o main_window.py main_window.ui

To add a new screen to the project:

1. In Qt Creator choose New File or Project from the File menu.
2. In the Files and Classes: Qt section, choose Qt Designer Form.
3. Select a widget type, like "Widget", and choose a file name.

To edit image files or other resources:

1. Edit the original files in the `resources` folder.
2. If you added new files, include them in `resources/resources.qrc`.
3. Compile all the resources into a Python module:

       $ cd /path/to/four-letter-blocks/resources
       $ pyside6-rcc -o ../four_letter_blocks/four_letter_blocks_rc.py resources.qrc

[Qt Creator]: https://www.qt.io/download-qt-installer
[Qt Designer documentation]: https://doc.qt.io/qt-5/designer-quick-start.html

## Testing GitHub Pages locally
The web site uses the [Bulma Clean theme], which is based on [Bulma]. The
[Bulma colours] can be particularly helpful to learn about.

GitHub generates all the web pages from markdown files, but it can be useful to
test out that process before you commit changes. See the detailed instructions
for setting up [Jekyll], but the main command is this:

    cd docs
    bundle exec jekyll serve

[Bulma Clean theme]: https://github.com/chrisrhymes/bulma-clean-theme
[Bulma]: https://bulma.io/documentation/
[Bulma colours]: https://bulma.io/documentation/overview/colors/
[Jekyll]: https://help.github.com/en/github/working-with-github-pages/testing-your-github-pages-site-locally-with-jekyll
