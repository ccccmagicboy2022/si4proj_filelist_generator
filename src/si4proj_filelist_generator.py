import os
from os import path
import re
import typer
from typing import Optional
from rich.traceback import install
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
import win32api
import win32con
import ctypes

IAR_PJ      =   0
KEIL4_PJ    =   1
KEIL5_PJ    =   2

global line_set
line_set = []
global ext_set
ext_set = ['.c', '.h', '.cpp', '.hpp', '.cs', '.py', '.m', '.v', '.json', '.xml']
global __version__
__version__ = "1.0.2"
global TargetName
TargetName = ''

def find_dep_file(url):
    global TargetName
    sourcefile = ''
    if path.isfile(url):
        ext = os.path.splitext(url)[-1].lower()
        if ext == '.eww':
            wsdtfile = os.path.join(os.path.split(url)[0], 'settings')
            wsdtfile = os.path.join(wsdtfile, os.path.split(url)[-1].replace('.eww', '.wsdt'))
            if os.path.exists(wsdtfile):
                tree = ET.ElementTree(file=wsdtfile)
                ConfigDictionary = tree.find('ConfigDictionary')
                CurrentConfigs = ConfigDictionary.find('CurrentConfigs')
                TargetName = CurrentConfigs.find('Project').text.split('/')[1]
                depfilename = CurrentConfigs.find('Project').text.split('/')[0] + '.dep'
                depfilename = os.path.join(os.path.split(url)[0], depfilename)
                if os.path.exists(depfilename):
                    return (depfilename, TargetName)
                else:
                    return ('', '')
            else:
                return ('', '')
        elif ext == '.uvproj' or ext == '.uvprojx':
            if ext == '.uvproj':
                uvoptfile = url.replace('.uvproj', '.uvopt')
            elif ext == '.uvprojx':
                uvoptfile = url.replace('.uvprojx', '.uvoptx')
            print(uvoptfile)
            tree = ET.ElementTree(file=uvoptfile)
            for tag in tree.findall('Target'):
                TargetOption = tag.find('TargetOption')
                OPTFL = TargetOption.find('OPTFL')
                IsCurrentTarget = int(OPTFL.find('IsCurrentTarget').text)
                if IsCurrentTarget:
                    TargetName = tag.find('TargetName').text
                    break
            Extensions = tree.find('Extensions')
            if None == Extensions.findtext('nMigrate'):
                # ide is keil4
                depfilename = os.path.splitext(url)[0] + '_' + TargetName + '.dep'
                if os.path.exists(depfilename):
                    sourcefile = depfilename
            else:
                # ide is keil5
                tree = ET.ElementTree(file=url)
                for tag in tree.find('Targets').findall('Target'):
                    if tag.find('TargetName').text == TargetName:
                        TargetOption = tag.find('TargetOption')
                        TargetCommonOption = TargetOption.find('TargetCommonOption')
                        OutputDirectory = TargetCommonOption.find('OutputDirectory').text
                        OutputDirectory = os.path.normpath(os.path.join(os.path.split(url)[0], OutputDirectory))
                        print(OutputDirectory)
                        depfilename = os.path.splitext(url)[0] + '_' + TargetName + '.dep'
                        depfilename = os.path.split(depfilename)[-1]
                        depfilename = os.path.join(OutputDirectory, depfilename)
                        print(depfilename)

                        if os.path.exists(depfilename):
                            sourcefile = depfilename
                            break
            return (sourcefile, TargetName)
        else:
            return ('', '')
    else:
        return ('', '')


def dep_to_list(uuu, url, mode, target_str):
    global line_set
    with open(url, 'r') as parsefile:
        if mode == IAR_PJ:
            tree = ET.ElementTree(file=parsefile)
            for tag in tree.findall('configuration'):
                if target_str == tag.find('name').text:
                    output_tag = tag.find('outputs')

                    for elem in output_tag.findall('file'):
                        if elem.text.startswith('$PROJ_DIR$'):
                            if elem.text.endswith('.c') or elem.text.endswith('.s') or elem.text.endswith('.h'):
                                line_set.append(os.path.abspath(elem.text.replace('$PROJ_DIR$', os.path.split(url)[0])))
                    break
        elif mode == KEIL4_PJ or mode == KEIL5_PJ:
            for line in parsefile.readlines():
                m = re.search(r"^F \(.*?\)|^I \(.*?\)", line)
                if None != m:
                    relpath = m.group(0)[3:-1]
                    line_set.append(os.path.abspath(os.path.join(os.path.split(uuu)[0], relpath)))

def save_list(url):
    global line_set
    if len(line_set):
        with open(url, 'w', encoding='utf-8') as f:
            f.write('; Source Insight Project File List\n')
            f.write('; Project Name: ' + url + '\n')
            f.write('; Generated by si4proj_filelist_generator at ' + datetime.now().strftime('%Y/%m/%d %H:%M:%S') + '\n')
            f.write('; Version: ' + __version__ + '\n')
            f.write('; Author: ' + 'cccc' + '\n')
            f.write(';\n')
            for ll in line_set:
                f.write(ll + '\n')
        typer.secho(f'{url} is saved!', fg=typer.colors.BRIGHT_WHITE, bg=typer.colors.YELLOW)

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
    else:
        ext = os.path.splitext(url)[-1].lower()
        if ext == '.eww':
            print('IAR Embedded Workbench IDE(IAR for Arm) project file: ')
            print(url)
            dep_name, target = find_dep_file(url)
            if dep_name != '':
                dep_to_list(url, dep_name, IAR_PJ, target)
            else:
                win32api.MessageBox(0, "build the IAR project first!!!", "warning", win32con.MB_ICONWARNING)
        elif ext == '.uvproj':
            print('Keil4 project file: ')
            print(url)
            dep_name, target = find_dep_file(url)
            if dep_name != '':
                dep_to_list(url, dep_name, KEIL4_PJ, target)
            else:
                win32api.MessageBox(0, "build the KEIL4 project first!!!", "warning", win32con.MB_ICONWARNING)
        elif ext == '.uvprojx':
            print('Keil5 project file: ')
            print(url)
            dep_name, target = find_dep_file(url)
            if dep_name != '':
                dep_to_list(url, dep_name, KEIL5_PJ, target)
            else:
                win32api.MessageBox(0, "build the KEIL5 project first!!!", "warning", win32con.MB_ICONWARNING)
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
    Simple program that generate the source insight 4 file list. Support c/c++ matlab python cs and keil/iar IDE project files.
    """
    path = os.path.abspath(path)
    scan_files(path)
    if os.path.isdir(path):
        if os.path.split(path)[-1] == '':
            save_list(os.path.join(path, os.path.split(path)[-2] + '_filelist.txt'))
        else:
            save_list(os.path.join(path, os.path.split(path)[-1] + '_filelist.txt'))
    else:
        save_list(os.path.join(os.path.split(path)[0], os.path.splitext(os.path.split(path)[-1])[0] + '_filelist.txt'))

if __name__ == '__main__':
    dll = ctypes.CDLL('shcore.dll')
    if dll:
        dll.SetProcessDpiAwareness(2)
    install()
    typer.run(main)
