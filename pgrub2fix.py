#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  pgrub2fix.py
#  
#  Copyright 2018 youcef sourani <youssef.m.sourani@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import dbus
import os
import time
import subprocess
import sys
import getpass



def get_distro_name(location):
    result=""
    if not os.path.isfile(location):
        return None
    with open(location) as myfile:
        for l in myfile:
            if l.startswith("ID") and not l.startswith("ID_"):
                result=l.split("=",1)[1].strip()
    return result.replace("\"","").replace("'","")

def get_distro_name_like(location):
    result=""
    if not os.path.isfile(location):
        return None
    with open(location) as myfile:
        for l in myfile:
            if l.startswith("ID_LIKE") :
                result=l.split("=",1)[1].strip()
    if not result:
        result = get_distro_name(location)
    return result.replace("\"","").replace("'","")
    
def get_distro_version(location):
    result=""
    if not os.path.isfile(location):
        return None
    with open(location) as myfile:
        for l in myfile:
            if l.startswith("VERSION_ID"):
                result=l.split("=",1)[1].strip()
    return result.replace("\"","").replace("'","")



def get_method(bus,bus_name,object_path,interface_path,method_name):
    try:
        bus    = dbus.SessionBus() if bus=="session" else dbus.SystemBus()
        proxy  = bus.get_object(bus_name,object_path)
        return proxy.get_dbus_method(method_name,interface_path)
    except Exception as e:
        print(e)
        return False
    
def get_propertie(bus,bus_name,object_path,interface_path,propertie_name):
    try:
        bus    = dbus.SessionBus() if bus=="session" else dbus.SystemBus()
        proxy  = bus.get_object(bus_name,object_path)
        return proxy.get_dbus_method("Get","org.freedesktop.DBus.Properties")(interface_path,propertie_name)
    except Exception as e:
        print(e)
        return False
        
def get_all_properties(bus,bus_name,object_path,interface_path):
    try:
        bus    = dbus.SessionBus() if bus=="session" else dbus.SystemBus()
        proxy  = bus.get_object(bus_name,object_path)
        return proxy.get_dbus_method("GetAll","org.freedesktop.DBus.Properties")(interface_path)
    except Exception as e:
        print(e)
        return False
        
def set_propertie(bus,bus_name,object_path,interface_path,propertie_name,propertie_value):
    try:
        bus    = dbus.SessionBus() if bus=="session" else dbus.SystemBus()
        proxy  = bus.get_object(bus_name,object_path)
        return proxy.get_dbus_method("Set","org.freedesktop.DBus.Properties")(interface_path,propertie_name,propertie_value)
    except Exception as e:
        print(e)
        return False 



class Partition(object):
    def __init__(self,object_path,lock=False):
        self.object_path = object_path
        self.lock        = lock
        self.ignore      = False

        if self.lock:
            if self.unlock():
                self.get_block_properties()
                self.get_filesystem_properties()
                self.get_path()
                self.get_mount_point()
                self.get_preferred_device()
                self.get_symlinks_path()
            else:
                self.ignore = True
        else:
            self.get_block_properties()
            self.get_filesystem_properties()
            self.get_path()
            self.get_mount_point()
            self.get_preferred_device()
            self.get_symlinks_path()
        
        
    def get_block_properties(self):
        properties = get_all_properties("system",
                                 "org.freedesktop.UDisks2",
                                 self.object_path,
                                 "org.freedesktop.UDisks2.Block")
        self.block_properties = properties
        for k,v in properties.items():
            self.__setattr__(k,v)
        return properties
        
    def get_filesystem_properties(self):
        properties = get_all_properties("system",
                                 "org.freedesktop.UDisks2",
                                 self.object_path,
                                 "org.freedesktop.UDisks2.Filesystem")
        self.filesystem_properties = properties
        for k,v in properties.items():
            self.__setattr__(k,v)
        return properties
    
    def mount(self,options):
        return get_method("system",
                          "org.freedesktop.UDisks2",
                          self.object_path,
                          "org.freedesktop.UDisks2.Filesystem",
                          "Mount")(options)

    def unmount(self,options):
        return get_method("system",
                          "org.freedesktop.UDisks2",
                          self.object_path,
                          "org.freedesktop.UDisks2.Filesystem",
                          "Unmount")(options)

    def get_passphrase(self,count=0,msg=""):
        subprocess.call("clear")
        if msg:
            print(msg)
        print("Enter Passphrase To Unlock Partition .\n")
        if count==3:
            return False
        if count==2:
            passphrase1 = input('Passphrase: ')
            passphrase2 = input('Retype Passphrase: ')
        else:
            passphrase1 = getpass.getpass('Passphrase: ')
            passphrase2 = getpass.getpass('Retype Passphrase: ')
        count += 1
        if not passphrase1 or not passphrase1:
            return self.get_passphrase(count,"Try Again.\n")
        elif passphrase1!=passphrase2:
            return self.get_passphrase(count,"Try Again.\n")
        return passphrase1
        
    def unlock(self,passphrase=None,options={"keyfile_contents":[0]}):
        properties      = get_all_properties("system",
                                             "org.freedesktop.UDisks2",
                                             self.object_path,
                                             "org.freedesktop.UDisks2.Encrypted")
        object_ = properties["CleartextDevice"]
        if object_.startswith("/org/freedesktop/UDisks2/block_devices"):
            self.object_path = object_
            return True
        try :
            if not passphrase:
                passphrase = self.get_passphrase()
            result = get_method("system",
                                "org.freedesktop.UDisks2",
                                self.object_path,
                                "org.freedesktop.UDisks2.Encrypted",
                                "Unlock")(passphrase,options)
        except Exception as e:
            print(e)
            return False
        properties      = get_all_properties("system",
                                             "org.freedesktop.UDisks2",
                                             self.object_path,
                                             "org.freedesktop.UDisks2.Encrypted")
        object_ = properties["CleartextDevice"]
        self.object_path = object_
        return True

    def check(self,options):
        return get_method("system",
                          "org.freedesktop.UDisks2",
                          self.object_path,
                          "org.freedesktop.UDisks2.Filesystem",
                          "Check")(options)

    def repair(self,options):
        return get_method("system",
                          "org.freedesktop.UDisks2",
                          self.object_path,
                          "org.freedesktop.UDisks2.Filesystem",
                          "Repair")(options)
                          
    def get_path(self):
        device = self.Device
        if device:
            if device[-1] == 0:
                device = device[:-1]
        self.device_path = "".join([chr(i) for i in device])
        return self.device_path
        
    def get_preferred_device(self):
        preferred_device = self.PreferredDevice
        if preferred_device:
            if preferred_device[-1] == 0:
                preferred_device = preferred_device[:-1]
        self.preferred_device = "".join([chr(i) for i in preferred_device])
        return self.preferred_device
        
    def get_mount_point(self):
        mountpoint = self.MountPoints
        if mountpoint:
            mountpoint = mountpoint[0]
            if mountpoint[-1] == 0:
                mountpoint = mountpoint[:-1]
        else:
            self.mount_point = ""
            return ""
        self.mount_point = "".join([chr(i) for i in mountpoint])
        return self.mount_point
        
    def get_symlinks_path(self):
        symlinks_path = self.Symlinks
        if symlinks_path:
            symlinks_path = symlinks_path[0]
            if symlinks_path[-1] == 0:
                symlinks_path = symlinks_path[:-1]
        else:
            self.symlinks_path = ""
            return ""
        self.symlinks_path = "".join([chr(i) for i in symlinks_path])
        return self.symlinks_path


class Device(object):
    def __init__(self,object_path):
        self.object_path = object_path
        
        self.get_block_properties()
        self.get_partition_table_properties()
        self.isremovable()
        self.get_path()
        
    def get_block_properties(self):
        properties = get_all_properties("system",
                                 "org.freedesktop.UDisks2",
                                 self.object_path,
                                 "org.freedesktop.UDisks2.Block")
        self.block_properties = properties
        for k,v in properties.items():
            self.__setattr__(k,v)
        return properties
        
    def get_partition_table_properties(self):
        properties = get_all_properties("system",
                                 "org.freedesktop.UDisks2",
                                 self.object_path,
                                 "org.freedesktop.UDisks2.PartitionTable")
        self.partition_table_properties = properties
        for k,v in properties.items():
            self.__setattr__(k,v)
        return properties
    
    def isremovable(self):
        drive_path_object = self.Drive
        result            =  get_propertie("system",
                                           "org.freedesktop.UDisks2",
                                           drive_path_object,
                                           "org.freedesktop.UDisks2.Drive",
                                           "Removable")
                                           
        self.Removable = False if result==0 else True
        return self.Removable
        
    def get_path(self):
        device = self.Device
        if device:
            if device[-1] == 0:
                device = device[:-1]
        self.drive_path = "".join([chr(i) for i in device])
        return self.drive_path





"""def get_all_device_with_partitions(include_removable=False,
                                   filesystem=False,#list
                                   ignore_filesystem=False,#list
                                   ignore_fstab=True,
                                   ignore_mounted=False,
                                   ignore_readonly=False):
    devices         = []
    result          = {}
    managed_objects = get_method("system",
                                 "org.freedesktop.UDisks2",
                                 "/org/freedesktop/UDisks2",
                                 "org.freedesktop.DBus.ObjectManager",
                                 "GetManagedObjects")()
    
    for k,v in managed_objects.items():
        if "org.freedesktop.UDisks2.PartitionTable" in v.keys():
            devices.append(Device(k))
    
    if not include_removable:
        devices = [d for d in devices if not d.Removable]
            
    for d in devices:
        result.setdefault(d.drive_path,list())
        for p in d.Partitions:
            if "org.freedesktop.UDisks2.Filesystem" in managed_objects[p].keys():
                part = Partition(p)
                if ignore_fstab:
                    if part.Configuration:
                        continue
                if ignore_filesystem:
                    if part.IdType in ignore_filesystem:
                        continue
                if ignore_mounted:
                    if part.MountPoints:
                        continue
                if ignore_readonly:
                    if part.ReadOnly:
                        continue
                        
                if filesystem:
                    if not "all" in filesystem:
                        if part.IdType not in filesystem:
                            continue
                result[d.drive_path].append(part)

    return result"""

def get_all_device(include_removable=False):
    devices  = {}
    count    = 1
    managed_objects = get_method("system",
                                 "org.freedesktop.UDisks2",
                                 "/org/freedesktop/UDisks2",
                                 "org.freedesktop.DBus.ObjectManager",
                                 "GetManagedObjects")()
    
    for k,v in managed_objects.items():
        if "org.freedesktop.UDisks2.PartitionTable" in v.keys():
            d = Device(k)
            if not include_removable:
                if not d.Removable:
                    devices.setdefault(str(count),d.drive_path)
                    count += 1
            else:
                devices.setdefault(str(count),d.drive_path)
                count += 1
    return devices
    
def get_partitions(filesystem=False,#list
                   ignore_filesystem=False,#list
                   ignore_fstab=True,
                   ignore_mounted=False,
                   ignore_readonly=False):
                    
    result          = {}
    managed_objects = get_method("system",
                                 "org.freedesktop.UDisks2",
                                 "/org/freedesktop/UDisks2",
                                 "org.freedesktop.DBus.ObjectManager",
                                 "GetManagedObjects")()
    
    for k,v in managed_objects.items():
        if "org.freedesktop.UDisks2.Filesystem" in v.keys() or "org.freedesktop.UDisks2.Encrypted" in v.keys():
            if "org.freedesktop.UDisks2.Encrypted" in v.keys():
                part = Partition(k,True)
                if part.ignore:
                    continue
            else:
                part = Partition(k)
            if ignore_fstab:
                if part.Configuration:
                    continue
            if ignore_filesystem:
                if part.IdType in ignore_filesystem:
                    continue
            if ignore_mounted:
                if part.MountPoints:
                    continue
            if ignore_readonly:
                if part.ReadOnly:
                    continue
            if filesystem:
                if not "all" in filesystem:
                    if part.IdType not in filesystem:
                        continue
            result.setdefault(part.preferred_device,part)

    return result
    
def get_all_info(timeout=2):
    result = {
               "root"  : {},
               "boot"  : {},
               "efi"   : {},
               "other" : {},
    }
    count   = 1
    count1  = 1
    count2  = 1
    count3  = 1
    
    for preferred_device,partition in get_partitions(ignore_filesystem=["ntfs"]).items():
        try:
            if partition.mount_point:
                time.sleep(timeout)
                partition.unmount(dict())
                time.sleep(timeout)
        except Exception as e:
            #print(e)
            continue
            
        try:
            location = partition.mount(dict())
        except Exception as e:
            #print(e)
            continue
        
        if os.path.isfile(os.path.join(location,"etc/os-release")):
            distro_name      = get_distro_name(os.path.join(location,"etc/os-release")) 
            distro_version   = get_distro_version(os.path.join(location,"etc/os-release"))
            result["root"].setdefault(str(count),("({} {}) {}".format(distro_name,distro_version,preferred_device),partition))
            count += 1
            time.sleep(timeout)
            partition.unmount(dict())
            #time.sleep(timeout)

        elif os.path.isdir(os.path.join(location,"boot"))  and not os.path.isdir(os.path.join(location,"etc")):
            result["boot"].setdefault(str(count1),(preferred_device,partition))
            count1 += 1
            time.sleep(timeout)
            partition.unmount(dict())
            #time.sleep(timeout)

        elif os.path.isdir(os.path.join(location,"EFI")) :
            result["efi"].setdefault(str(count2),(preferred_device,partition))
            count2 += 1
            time.sleep(timeout)
            partition.unmount(dict())
            #time.sleep(timeout)

        """else:
            result["other"].setdefault(str(count3),(preferred_device,partition))
            count3 += 1
            time.sleep(timeout)
            partition.unmount(dict())
            #time.sleep(timeout)"""
    
    if result["boot"]:
        result["boot"].setdefault(str(count1),("None","None"))
    if result["efi"]:
        result["efi"].setdefault(str(count2),("None","None"))
    return result

def get_ch(msg,dic,key):
    blacklist = []
    while True:
        os.system("clear")
        print(home_page)
        print(msg)
        for k,v in dic[key].items():
            if "loop"  in v[0]:
                blacklist.append(k)
                continue
            print("{}-{}\n".format(k,v[0]))
        answer = input("\n- ").strip()
        if answer=="q" or answer=="Q":
            print("\nbye...\n")
            exit(4)
        elif answer in dic[key].keys() and answer not in blacklist:
            if dic[key][answer][-1] == "None":
                return False
            return dic[key][answer][-1]

def get_device_path(msg,dic):
    while True:
        os.system("clear")
        print(home_page)
        print(msg)
        for k,v in dic.items():
            print("{}-{}\n".format(k,v))
        answer = input("\n- ").strip()
        if answer=="q" or answer=="Q":
            print("\nbye...\n")
            exit(4)
        elif answer in dic.keys():
            return dic[answer]

def get_choice(msg):
    yes = ["y","Y","yes","YES"]
    no =  ["n","N","no","NO"]
    while True:
        os.system("clear")
        print(home_page)
        print(msg)
        answer = input("\n- ").strip()
        if answer=="q" or answer=="Q":
            print("\nbye...\n")
            exit(4)
        elif answer in yes:
            return True
        elif answer in no:
            return False
            
def mount_all(to_mount,timeout=2,use_internet=False):
    efi = False
    for v in to_mount.values():
        if v[0]=="r":
            try:
                mount_point = v[-1].mount(dict())
            except Exception as e:
                print(e)
                exit(1)
        elif v[0]=="b":
            if subprocess.call("mount -B {} {}".format(v[-1].device_path,os.path.join(mount_point,"boot")),shell=True)!=0:
                print("'mount -B {} {}' Failed.".format(v[-1].device_path,os.path.join(mount_point,"boot")))
                subprocess.call("umount -R {}".format(mount_point),shell=True)
                exit(1)
        elif v[0]=="e":
            efi = True
            if subprocess.call("mount -B {} {}".format(v[-1].device_path,os.path.join(mount_point,"boot/EFI")),shell=True)!=0:
                print("'mount -B {} {}' Failed.".format(v[-1].device_path,os.path.join(mount_point,"boot/EFI")))
                subprocess.call("umount -R {}".format(mount_point),shell=True)
                exit(1)
                
        time.sleep(timeout)
    
    for l in  ["dev","sys","proc","dev/pts","run"] :
        if subprocess.call("mount -B /{} {}".format(l,os.path.join(mount_point,l)),shell=True)!=0:
            print("'mount -B /{} {}' Failed.".format(l,os.path.join(mount_point,l)))
            subprocess.call("umount -R {}".format(mount_point),shell=True)
            exit(1)
        time.sleep(timeout)
    if use_internet:
        if os.path.isfile("/etc/resolv.conf"):
            if subprocess.call("mount -B /etc/resolv.conf {}".format(os.path.join(mount_point,"etc/resolv.conf")),shell=True)!=0:
                print("'mount -B /etc/resolv.conf {}' Failed.".format(os.path.join(mount_point,"etc/resolv.conf")))
                subprocess.call("umount -R {}".format(mount_point),shell=True)
                exit(1)
        
        
    return (mount_point,efi)
    
def fix_grub(mount_point,efi,drive_path,use_internet,install_kernel):
    failed = False
    os.system("clear")
    print(home_page)
    print("\nPlease Wait...\n")
    if "fedora" in get_distro_name_like(os.path.join(mount_point,"etc/os-release")).lower() :
        grub_install  = "grub2-install"                 #for other distro change this ex :grub-install
        grub_mkconfig = "grub2-mkconfig"                #for other distro change this ex :grub-mkconfig
        legacy_path   = "/boot/grub2/grub.cfg"          #for other distro change this ex :/boot/grub/grub.cfg
        uefi_path     = "/boot/efi/EFI/fedora/grub.cfg" #for other distro change this ex :/boot/grub/grub.cfg
        legacy_command= ["dnf install     os-prober  grub2  --best -y --setopt=strict=0",
                         "dnf reinstall   os-prober  grub2  --best -y --setopt=strict=0"]  #run if use_internet True
        efi_command   = ["dnf install   shim os-prober efibootmgr grub2 grub2-efi*  --best -y --setopt=strict=0", \
                         "dnf reinstall shim os-prober efibootmgr grub2 grub2-efi*  --best -y --setopt=strict=0"] #run if use_internet True
        if install_kernel:
            legacy_command.append("dnf install kernel  --best -y --setopt=strict=0")
            legacy_command.append("dnf reinstall kernel  --best -y --setopt=strict=0")
            efi_command.append("dnf install kernel  --best -y --setopt=strict=0")
            efi_command.append("dnf reinstall kernel  --best -y --setopt=strict=0")
                     
    elif "ubuntu" in get_distro_name_like(os.path.join(mount_point,"etc/os-release")).lower() :
        grub_install  = "grub-install"                  #for other distro change this ex :grub-install
        grub_mkconfig = "grub-mkconfig"                 #for other distro change this ex :grub-mkconfig
        legacy_path   = "/boot/grub/grub.cfg"           #for other distro change this ex :/boot/grub/grub.cfg
        uefi_path     = "/boot/grub/grub.cfg"           #for other distro change this ex :/boot/grub/grub.cfg
        
        legacy_command= []  #run if use_internet True
        efi_command   = [] #run if use_internet True
        #if install_kernel:
         #   legacy_command.append("")
         #   legacy_command.append("")
         #   efi_command.append("")
         #   efi_command.append("")

    elif "arch" in get_distro_name_like(os.path.join(mount_point,"etc/os-release")).lower() :
        grub_install  = "grub-install"                  #for other distro change this ex :grub-install
        grub_mkconfig = "grub-mkconfig"                 #for other distro change this ex :grub-mkconfig
        legacy_path   = "/boot/grub/grub.cfg"           #for other distro change this ex :/boot/grub/grub.cfg
        uefi_path     = "/boot/grub/grub.cfg"           #for other distro change this ex :/boot/grub/grub.cfg
        
        legacy_command= []  #run if use_internet True
        efi_command   = [] #run if use_internet True
        #if install_kernel:
         #   legacy_command.append("")
         #   legacy_command.append("")
         #   efi_command.append("")
         #   efi_command.append("")

    elif "opensuse" in get_distro_name_like(os.path.join(mount_point,"etc/os-release")).lower() :
        grub_install  = "grub2-install"                 #for other distro change this ex :grub-install
        grub_mkconfig = "grub2-mkconfig"                #for other distro change this ex :grub-mkconfig
        legacy_path   = "/boot/grub2/grub.cfg"          #for other distro change this ex :/boot/grub/grub.cfg
        uefi_path     = "/boot/grub2/grub.cfg"          #for other distro change this ex :/boot/grub/grub.cfg
        
        legacy_command= []  #run if use_internet True
        efi_command   = [] #run if use_internet True
        #if install_kernel:
         #   legacy_command.append("")
         #   legacy_command.append("")
         #   efi_command.append("")
         #   efi_command.append("")

    else:
        grub_install  = "grub-install"                  #for other distro change this ex :grub-install
        grub_mkconfig = "grub-mkconfig"                 #for other distro change this ex :grub-mkconfig
        legacy_path   = "/boot/grub/grub.cfg"           #for other distro change this ex :/boot/grub/grub.cfg
        uefi_path     = "/boot/grub/grub.cfg"           #for other distro change this ex :/boot/grub/grub.cfg
        
        legacy_command= []  #run if use_internet True
        efi_command   = [] #run if use_internet True
        #if install_kernel:
         #   legacy_command.append("")
         #   legacy_command.append("")
         #   efi_command.append("")
         #   efi_command.append("")

    try:
        real_root    = os.open("/", os.O_RDONLY)
        os.chroot(mount_point)
        os.makedirs("/boot",exist_ok=True)
        os.chdir("/boot")
        if efi:
            if use_internet:
                for c in efi_command:
                    subprocess.call(c,shell=True)
            if subprocess.call("{} {}".format(grub_install,drive_path),shell=True)!=0:
                raise Exception("Run '{} {}' Failed.".format(grub_install,drive_path))
        
            if subprocess.call("{} -o {}".format(grub_mkconfig,efi_path),shell=True)!=0:
                raise Exception("{} -o {}".format(grub_mkconfig,efi_path))
        else:
            if use_internet:
                for c in legacy_command:
                    subprocess.call(c,shell=True)
            if subprocess.call("{} {}".format(grub_install,drive_path),shell=True)!=0:
                raise Exception("Run '{} {}' Failed.".format(grub_install,drive_path))
            if subprocess.call("{} -o {}".format(grub_mkconfig,legacy_path),shell=True)!=0:
                raise Exception("{} -o {}".format(grub_mkconfig,legacy_path))
    except Exception as e:
        failed = True
        print(e)
    finally:
        try:
            os.fchdir(real_root)
            os.chroot(".")
            os.close(real_root)
            subprocess.call("umount -R {}".format(mount_point),shell=True)
        except:
            pass
            
    if failed :
        print("Failed")
    else:
        print("\n\nFinish\n")
    
def command_main():
    to_mount = {}
    os.system("clear")
    print(home_page)
    print("\nPlease Wait...\n")
    all_info = get_all_info()
    count = 1
    if not all_info["root"]:
        print("\nNo Root Partition Found.\n")
        exit(3)
    root = get_ch("\nq To Quit || Choice Root Partition :\n",all_info,"root")
    to_mount.setdefault(str(count),("r",root))
    count += 1
    
    if all_info["boot"]:
        boot = get_ch("\nq To Quit || Choice Boot Partition :\n",all_info,"boot")
        if boot:
            to_mount.setdefault(str(count),("b",boot))
            count += 1
            
    if all_info["efi"]:
        efi = get_ch("\nq To Quit || Choice EFI Partition :\n",all_info,"efi")
        if efi:
            to_mount.setdefault(str(count),("e",efi))
            count += 1
            
    drive_path     = get_device_path("\nq To Quit || Choice Device To Install Grub2 :\n",get_all_device())
    use_internet   = get_choice("\nq To Quit || Do You Need Use Internet To Reinstall grub/kernel/os-prober If Needed (y/n)?")
    if use_internet:
        install_kernel = get_choice("\nq To Quit || Do You Need Install Kernel y/n ?")
    else:
        install_kernel = False
    os.system("clear")
    print(home_page)
    print("\nPlease Wait...\n")
    mount_point_info = mount_all(to_mount,use_internet=use_internet)
    fix_grub(mount_point_info[0],efi=mount_point_info[-1],drive_path=drive_path,use_internet=use_internet,install_kernel=install_kernel)

def gui_main():
    print("Not Ready Right Now.")
    pass

if __name__ == "__main__":
    if os.getuid()!=0:
        print("\nRun Script With Root Permissions.\n")
        exit()
    home_page = "https://github.com/yucefsourani/pgrub2fix"
    if "--gui" in sys.argv or "-g" in sys.argv:
        gui_main()
    else:
        command_main()
