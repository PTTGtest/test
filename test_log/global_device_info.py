# -*- coding: utf-8 -*-
import json
import os
from threading import Lock

from ppadb.device import Device

from settings import logger, RESULT_LOG_DIR, SPRD_APPS_VERSION_SUFFIX, SPRD_SDK_INT_SUFFIX, SPRD_ROM_VERSION_SUFFIX

registered_device_info = {}
app_version_name_file = '/data/local/tmp/app_version_name.txt'
dump_app_version_name = "for i in $(for i in $(pm list packages); do echo ${i:8};done);" \
                        "do versionName=$(pm dump $i | grep versionName); echo $i ${versionName:16};done"

init_locks = {}


def init_device_info_from_device(device: Device):
    serial = device.serial
    lock: Lock = init_locks.get(serial, None)
    if lock:
        with lock:
            logger.debug("初始化 {} 已经在执行中了， 等待完成".format(serial))
            return registered_device_info.get(serial, None)
    else:
        init_serial_lock = Lock()
        init_locks[serial] = init_serial_lock

        with init_serial_lock:
            info = DeviceInfo()
            info.init_app_versions(device)
            info.init_sdk_int(device)
            info.init_device_rom_version(device)
            if info.valid():
                logger.debug("初始化 {} 信息成功".format(serial))
                registered_device_info[serial] = info
                logger.debug("保存 {} 设备信息".format(serial))
                save_info(serial, info)
            else:
                logger.debug("初始化 {} 信息失败".format(serial))

            return info


def init_device_info_from_files(serial, apps_version_file: str, sdk_int_file: str, rom_version_file: str):
    info = DeviceInfo()
    with open(sdk_int_file, 'rb') as f:
        sdk_int = int(f.read())
        info.sdk_int = sdk_int

    with open(apps_version_file, 'rb') as f:
        versions = f.read()
        info.app_version_names = json.loads(versions)

    with open(rom_version_file, 'rb') as f:
        rom_version = f.read()
        info.rom_version = json.loads(rom_version)

    registered_device_info[serial] = info


def get_device_info(serial: str, device=None):
    info: DeviceInfo = registered_device_info.get(serial, None)
    # logger.debug("获取 {} 信息 {}".format(serial, info.valid() if info else False))
    return info


def save_info(serial: str, info):
    device_serial_dir = os.path.join(RESULT_LOG_DIR, serial)
    os.makedirs(device_serial_dir, exist_ok=True)
    save_info_file = os.path.join(device_serial_dir, '{}{}'.format(serial, SPRD_APPS_VERSION_SUFFIX))

    with open(save_info_file, 'wb+') as sf:
        app_version_names = json.dumps(info.get_app_version_names(), indent=2)
        sf.write(app_version_names.encode('utf-8'))

    save_sdk_int_file = os.path.join(device_serial_dir, '{}{}'.format(serial, SPRD_SDK_INT_SUFFIX))
    with open(save_sdk_int_file, 'wb+') as sf:
        device_sdk_int = info.get_sdk_int()
        sf.write('{}'.format(device_sdk_int).encode('utf-8'))

    save_rom_version_file = os.path.join(device_serial_dir, '{}{}'.format(serial, SPRD_ROM_VERSION_SUFFIX))
    with open(save_rom_version_file, 'wb+') as sf:
        device_rom_version = json.dumps(info.get_device_rom_version(), indent=2)
        sf.write(device_rom_version.encode('utf-8'))

    return info


class DeviceInfo:
    def __init__(self):
        self.app_version_names = {}
        self.sdk_int = -1
        self.rom_version = {}

    def init_sdk_int(self, device: Device):
        logger.debug("初始化 {} sdk int".format(device.serial))
        output: str = device.shell("getprop ro.build.version.sdk")
        output = output.replace('\n', '')
        self.sdk_int = int(output)
        logger.debug("初始化 {} sdk int完成, 值 {}".format(device.serial, self.sdk_int))

    def init_device_rom_version(self, device: Device):
        logger.debug("初始化 {} rom version".format(device.serial))
        output: str = device.shell("getprop ro.build.display.id")
        output = output.replace('\n', '')
        self.rom_version[device.serial] = output
        logger.debug("初始化 {} rom version完成".format(device.serial))
        logger.debug(self.rom_version)

    def init_app_versions(self, device: Device):
        logger.debug("初始化 {} app版本号".format(device.serial))
        for package_name in device.list_packages():
            try:
                version_name = device.get_package_version_name(package_name)
                self.app_version_names[package_name] = version_name
            except AttributeError:
                pass
        logger.debug("初始化 {} app版本号完成".format(device.serial))
        logger.debug(self.app_version_names)

    def valid(self):
        return self.app_version_names and \
               self.sdk_int > 0

    def get_sdk_int(self):
        return self.sdk_int

    def get_app_version_names(self):
        return self.app_version_names

    def get_device_rom_version(self):
        return self.rom_version

    def get_device_rom_version_name(self, device_serial):
        return self.rom_version.get(device_serial, None)

    def get_app_version_name(self, app_package):
        return self.app_version_names.get(app_package, None)


if __name__ == '__main__':
    from ppadb.client import Client

    cli = Client()
    any_device = cli.devices()[0]
    dinfo = DeviceInfo()
    dinfo.init_app_versions(any_device)
    dinfo.init_sdk_int(any_device)
    print(dinfo.valid())
