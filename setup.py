from distutils.core import setup
import shutil
import distutils.command.install_scripts


class StripDot(distutils.command.install_scripts.install_scripts):
    def run(self):
        distutils.command.install_scripts.install_scripts.run(self)
        out_files = self.get_outputs()
        for i, script in enumerate(out_files):
            if script.endswith(".py"):
                newname = script[:-3]
                shutil.move(script, newname)
                out_files[i] = newname


if __name__ == '__main__':
    setup(
        name='jam',
        version='0.3.0',
        description='JSON Mongo-like filter',
        author='dstarod',
        author_email='dmitry.starodubcev@gmail.com',
        scripts=[
            'jam.py',
        ],
        cmdclass={"install_scripts": StripDot}
    )
