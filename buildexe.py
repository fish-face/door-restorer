# This will create a dist directory containing the executable file, all the data
# directories. All Libraries will be bundled in executable file.
#
# Run the build process by entering 'pygame2exe.py' or
# 'python pygame2exe.py' in a console prompt.
#
# To build exe, python, pygame, and py2exe have to be installed. After
# building exe none of this libraries are needed.
#Please Note have a backup file in a different directory as if it crashes you
#will loose it all!(I lost 6 months of work because I did not do this)


try:
    from distutils.core import setup
    import py2exe, pygame
    from modulefinder import Module
    import glob, fnmatch
    import sys, os, shutil
    import operator
    import zipfile
except ImportError, message:
    raise SystemExit,  "Unable to load module. %s" % message

sys.path.append(os.path.join('.', 'src'))
sys.path.insert(0, os.path.join('.', 'PyTMX'))

#hack which fixes the pygame mixer and pygame font
origIsSystemDLL = py2exe.build_exe.isSystemDLL # save the orginal before we edit it
def isSystemDLL(pathname):
    # checks if the freetype and ogg dll files are being included
    if os.path.basename(pathname).lower() in ("libfreetype-6.dll", "libogg-0.dll","sdl_ttf.dll"): # "sdl_ttf.dll" added by arit.
            return 0
    return origIsSystemDLL(pathname) # return the orginal function
py2exe.build_exe.isSystemDLL = isSystemDLL # override the default function with this one

class pygame2exe(py2exe.build_exe.py2exe): #This hack make sure that pygame default font is copied: no need to modify code for specifying default font
    def copy_extensions(self, extensions):
        #Get pygame default font
        pygamedir = os.path.split(pygame.base.__file__)[0]
        pygame_default_font = os.path.join(pygamedir, pygame.font.get_default_font())

        #Add font to list of extension to be copied
        extensions.append(Module("pygame.font", pygame_default_font))
        py2exe.build_exe.py2exe.copy_extensions(self, extensions)

class BuildExe:
    def __init__(self):
        #Name of starting .py
        self.script = "launch.py"

        #Name of program
        self.project_name = "Dora"

        #Project url
        self.project_url = "http://www.github.com/fish-face/door-restorer"

        #Version of program
        self.project_version = "0.3"

        #License of the program
        self.license = "MIT"

        #Auhor of program
        self.author_name = "Chris 'Fish-Face' Le Sueur"
        self.author_email = "thefishface@gmail.com"
        self.copyright = "Copyright (c) 2014 Chris Le Sueur."

        #Description
        self.project_description = "Door-placing tile-based puzzle game"

        #Icon file (None will use pygame default icon)
        self.icon_file = None

        #Extra files/dirs copied to game
        self.extra_datas = ['levels', 'graphics', 'fonts', 'sounds']

        #Extra/excludes python modules
        self.extra_modules = []
        self.exclude_modules = []

        #DLL Excludes
        self.exclude_dll = ['']
        #python scripts (strings) to be included, seperated by a comma
        self.extra_scripts = []

        #Zip file name (None will bundle files in exe instead of zip file)
        self.zipfile_name = None

        #Dist directory
        self.dist_dir ='win32'

        #Whether to zip up the output
        self.create_zip = True

    ## Code from DistUtils tutorial at http://wiki.python.org/moin/Distutils/Tutorial
    ## Originally borrowed from wxPython's setup and config files
    def opj(self, *args):
        path = os.path.join(*args)
        return os.path.normpath(path)

    def find_data_files(self, srcdir, wildcards, recursive=True, **kw):
        # get a list of all files under the srcdir matching wildcards,
        # returned in a format to be used for install_data
        def walk_helper(arg, dirname, files):
            if '.svn' in dirname:
                return
            names = []
            lst, wildcards = arg
            for wc in wildcards:
                wc_name = self.opj(dirname, wc)
                for f in files:
                    filename = self.opj(dirname, f)

                    if fnmatch.fnmatch(filename, wc_name) and not os.path.isdir(filename):
                        names.append(filename)
            if names:
                lst.append( (dirname, names ) )

        file_list = []
        if recursive:
            os.path.walk(srcdir, walk_helper, (file_list, wildcards))
        else:
            walk_helper((file_list, wildcards),
                        srcdir,
                        [os.path.basename(f) for f in glob.glob(self.opj(srcdir, '*'))])
        return file_list

    def run(self):
        if os.path.isdir(self.dist_dir): #Erase previous destination dir
            shutil.rmtree(self.dist_dir)

        #Use the default pygame icon, if none given
        if self.icon_file == None:
            path = os.path.split(pygame.__file__)[0]
            self.icon_file = os.path.join(path, 'pygame.ico')

        #List all data files to add
        extra_datas = []
        for data in self.extra_datas:
            if os.path.isdir(data):
                extra_datas.extend(self.find_data_files(data, ['*'], recursive=False))
            else:
                extra_datas.append(('.', [data]))

        setup(
            cmdclass = {'py2exe': pygame2exe},
            version = self.project_version,
            description = self.project_description,
            name = self.project_name,
            url = self.project_url,
            author = self.author_name,
            author_email = self.author_email,
            license = self.license,
            # targets to build
            windows = [{
                'script': self.script,
                'icon_resources': [(0, self.icon_file)],
                'copyright': self.copyright
            }],
            options = {'py2exe': {'optimize': 2, 'bundle_files': 1, 'compressed': True, \
                                  'excludes': self.exclude_modules, 'packages': self.extra_modules, \
                                  'dll_excludes': self.exclude_dll,
                                  'includes': self.extra_scripts,
                                  'dist_dir': self.dist_dir}
                                  },
            zipfile = self.zipfile_name,
            data_files = extra_datas,
            )

        if os.path.isdir('build'): #Clean up build dir
            shutil.rmtree('build')

        if self.create_zip:
            z = zipfile.ZipFile('%s.zip' % (self.project_name), mode='w')
            for base, dirs, files in os.walk(self.dist_dir):
                for file in files:
                    dirname = base.replace(self.dist_dir, self.project_name, 1)
                    filename = os.path.join(base, file)
                    z.write(filename, arcname=os.path.join(dirname, file))

if __name__ == '__main__':
    if operator.lt(len(sys.argv), 2):
        sys.argv.append('py2exe')
    BuildExe().run() #Run generation
