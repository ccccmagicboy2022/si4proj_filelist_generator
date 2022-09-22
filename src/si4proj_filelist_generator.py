import os
from os import path
import re
import typer
from typing import Optional
from rich.traceback import install
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

for entry in os.scandir():
    if entry.is_file():
        if entry.name.endswith('.eww'):
            projectfilename = entry.name

            # find current target
            wsdtfile = os.path.join(os.getcwd(), 'settings')
            wsdtfile = os.path.join(wsdtfile, entry.name.replace('.eww', '.wsdt'))

            if os.path.exists(wsdtfile):
                tree = ET.ElementTree(file=wsdtfile)
                ConfigDictionary = tree.find('ConfigDictionary')
                CurrentConfigs = ConfigDictionary.find('CurrentConfigs')
                TargetName = CurrentConfigs.find('Project').text.split('/')[1]

                depfilename = CurrentConfigs.find('Project').text.split('/')[0] + '.dep'
                if os.path.exists(depfilename):
                    sourcefile = depfilename
                    break

            print('Please build the project once')
            input()
            sys.exit(0)

        elif entry.name.endswith('.uvproj') or entry.name.endswith('.uvprojx'):
            projectfilename = entry.name

            if entry.name.endswith('.uvproj'):
                uvoptfile = entry.name.replace('.uvproj', '.uvopt')
            elif entry.name.endswith('.uvprojx'):
                uvoptfile = entry.name.replace('.uvprojx', '.uvoptx')

            tree = ET.ElementTree(file=uvoptfile)

            # find current target
            for tag in tree.findall('Target'):
                TargetOption = tag.find('TargetOption')
                OPTFL = TargetOption.find('OPTFL')
                IsCurrentTarget = int(OPTFL.find('IsCurrentTarget').text)
                if IsCurrentTarget:
                    TargetName = tag.find('TargetName').text
                    break

            # find dep file of current target
            Extensions = tree.find('Extensions')
            if None == Extensions.findtext('nMigrate'):
                # ide is keil4
                depfilename = os.path.splitext(projectfilename)[0] + '_' + TargetName + '.dep'
                if os.path.exists(depfilename):
                    sourcefile = depfilename

            else:
                # ide is keil5
                tree = ET.ElementTree(file=entry.name)
                for tag in tree.find('Targets').findall('Target'):
                    if tag.find('TargetName').text == TargetName:
                        TargetOption = tag.find('TargetOption')
                        TargetCommonOption = TargetOption.find('TargetCommonOption')
                        OutputDirectory = TargetCommonOption.find('OutputDirectory').text
                        OutputDirectory = os.path.normpath(os.path.join(os.getcwd(), OutputDirectory))

                        depfilename = os.path.splitext(projectfilename)[0] + '_' + TargetName + '.dep'
                        depfilename = os.path.join(OutputDirectory, depfilename)

                        if os.path.exists(depfilename):
                            sourcefile = depfilename
                            break

            if '' == sourcefile:
                print('Please build the project once')
                input()
                sys.exit(0)

            break

#2、parse the seleted dep file
parsefile = open(sourcefile, 'r')
si4filelist = []
if projectfilename.endswith('.eww'):
    tree = ET.ElementTree(file=parsefile)
    for tag in tree.findall('configuration'):
        if TargetName == tag.find('name').text:
            output_tag = tag.find('outputs')

            for elem in output_tag.findall('file'):
                if elem.text.startswith('$PROJ_DIR$'):
                    if elem.text.endswith('.c') or elem.text.endswith('.s') or elem.text.endswith('.h'):
                        si4filelist.append(os.path.abspath(elem.text.replace('$PROJ_DIR$', os.getcwd()))+'\n')
            break

elif projectfilename.endswith('.uvproj') or projectfilename.endswith('.uvprojx'):
    for line in parsefile.readlines():
        m = re.search(r"^F \(.*?\)|^I \(.*?\)", line)
        if None != m:
            relpath = m.group(0)[3:-1]
            si4filelist.append(os.path.abspath(relpath)+'\n')
    si4filelist = set(si4filelist)





#########################################################################
global line_set
line_set = []
global ext_set
ext_set = ['.c', '.h', '.cpp', '.hpp', '.cs', '.py', '.m', '.v']
global __version__
__version__ = "1.0.2"
install()

def find_dep_file(url):
    if path.isfile(url):
        ext = os.path.splitext(url)[-1].lower()
        if ext == '.eww':
            wsdtfile = os.path.join(os.path.split(url)[0], 'settings')
            wsdtfile = os.path.join(wsdtfile, url.replace('.eww', '.wsdt'))            
            if os.path.exists(wsdtfile):
                tree = ET.ElementTree(file=wsdtfile)
                ConfigDictionary = tree.find('ConfigDictionary')
                CurrentConfigs = ConfigDictionary.find('CurrentConfigs')
                TargetName = CurrentConfigs.find('Project').text.split('/')[1]
                depfilename = CurrentConfigs.find('Project').text.split('/')[0] + '.dep'
                if os.path.exists(depfilename):
                    return depfilename
                else:
                    return 'none'
            else:
                return 'none'
        elif ext == '':
            pass
        elif ext == '':
            pass
        else:
            pass
    else:
        return 'none'


def dep_to_list(url):
    global line_set
    pass
    pass

def save_list(url):
    global line_set
    with open(url, 'w', encoding='utf-8') as f:
        f.write('; Source Insight Project File List\n')
        f.write('; Project Name: ' + url + '\n')
        f.write('; Generated by si4proj_filelist_generator at ' + datetime.now().strftime('%Y/%m/%d %H:%M:%S') + '\n')
        f.write('; Version: ' + __version__ + '\n')
        f.write(';\n')
        f.write('; Each line should contain either a file name, a wildcard, or a sub-directory name.\n')
        f.write('; File paths are relative to the project source root directory.\n')
        f.write(';\n')
        f.writelines(line_set)
    print('{0} is saved!', url)

def scan_files(url):
    global line_set
    if path.isdir(url):
        file = os.listdir(url)
        for f in file:
            real_url = path.join(url, f)
            if path.isfile(real_url):
                ext = os.path.splitext(f)[-1].lower()
                for xx in ext_set:
                    if ext == xx:
                        print(real_url)
                        line_set.append(real_url)
                        pass
            elif path.isdir(real_url):
                scan_files(real_url)
            else:
                pass
        save_list(os.path.join(url, 'si4project_filelist_folder.txt'))
    else:
        ext = os.path.splitext(url)[-1].lower()
        if ext == '.eww':
            print('IAR Embedded Workbench IDE(IAR for Arm) project file: ')
            print(url)
            dep_name = find_dep_file(url)
            dep_to_list(dep_name)
            save_list(os.path.join(os.path.split(url)[-1], 'si4project_filelist_IAR.txt'))
            pass
        elif ext == '.uvproj':
            print('Keil4 project file: ')
            print(url)
            dep_name = find_dep_file(url)
            dep_to_list(dep_name)
            save_list(os.path.join(os.path.split(url)[-1], 'si4project_filelist_KEIL4.txt'))
            pass
        elif ext == '.uvprojx':
            print('Keil5 project file: ')
            print(url)
            dep_name = find_dep_file(url)
            dep_to_list(dep_name)
            save_list(os.path.join(os.path.split(url)[-1], 'si4project_filelist_KEIL5.txt'))
            pass
        else:
            typer.secho(f"Not support project file: {url}", fg=typer.colors.BRIGHT_WHITE, bg=typer.colors.RED)
            pass

def version_callback(value: bool):
    if value:
        typer.echo(f"Version: v{__version__}")
        raise typer.Exit()

def path_callback(value: str):
    typer.secho(f"{value} begin to process ... ", fg=typer.colors.BRIGHT_WHITE, bg=typer.colors.GREEN)
    return value
        
def main(version: Optional[bool] = typer.Option(None, "--version", '-v', callback=version_callback), path: str = typer.Option("./", '--path', '-p', prompt = "Paste your path of code", help="code search path", confirmation_prompt=True, callback=path_callback)):
    """
    Simple program that generate the source insight 4 file list. 
    Support c/c++ matlab python cs.
    """
    scan_files(path)

if __name__ == '__main__':
    typer.run(main)
