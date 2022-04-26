import os, sys, subprocess, time

if os.system("ping www.archlinux.org -c 1 &> /dev/null") != 0:
    print("[ERROR]Not connected to a network. Connect to a wired connection and try again.")
    sys.exit(1)

inskde = input("Install kde plasma [y/n](default=n): ")
if inskde.lower() != "y" or inskde.lower() != "n": inskde = "n"

devList = subprocess.check_output("lsblk -o NAME,TYPE | grep disk | sed 's,disk,,g'", shell=True).decode().split()
try:
    d = subprocess.check_output("dmesg | grep -q 'EFI v'", shell=True)
    isuefi = True
except subprocess.CalledProcessError: isuefi = False
del d

if len(devList) == 0:
    print("[FATAL]No devices available.")
    sys.exit(1)
elif len(devList) == 1:
    if isuefi: os.system(f"parted /dev/{devList[0]} mklabel gpt")
    else: os.system(f"parted /dev/{devList[0]} mklabel msdos")
    os.system(f"parted /dev/{devList[0]} mkpart primary fat32 1MiB 257MiB")
    os.system(f"parted /dev/{devList[0]} mkpart primary linux-swap 257MiB 4353MiB")
    os.system(f"parted /dev/{devList[0]} mkpart primary ext4 4353MiB 100%")
    dev = devList[0]
else:
    o = "Available devices\n"
    i = 0
    for dev in devList:
        o += f"{i}) /dev/{dev}\n"
        i += 1
    print(o)
    while True:
        try:
            seldev = int(input("Type device number here (default=0): "))
            if seldev > len(devList)-1 or seldev < 0: print("Invalid input")
            else: break
        except ValueError: print("Invalid input")
    if ifuefi: os.system(f"parted /dev/{devList[seldev]} mklabel gpt")
    else: os.system(f"parted /dev/{devList[seldev]} mklabel msdos")
    os.system(f"parted /dev/{devList[seldev]} mkpart primary fat32 1MiB 257MiB")
    os.system(f"parted /dev/{devList[seldev]} mkpart primary linux-swap 257MiB 4353MiB")
    os.system(f"parted /dev/{devList[seldev]} mkpart primary ext4 4353MiB 100%")
    dev = devList[seldev]
os.system("systemctl daemon-reload")
if dev == "nvme0n1":
    p1 = "nvme0n1p1"
    p2 = "nvme0n1p2"
    p3 = "nvme0n1p3"
else:
    p1 = dev + "1"
    p2 = dev + "2"
    p3 = dev + "3"
os.system(f"mkfs.fat -F 32 /dev/{p1}")
os.system(f"mkswap /dev/{p2}")
os.system(f"swapon /dev/{p2}")
os.system(f"mkfs.ext4 /dev/{p3}")
os.system(f"mount /dev/{p3} /mnt")
if isuefi:
    os.system("mkdir -p /mnt/boot/efi")
    os.system(f"mount /dev/{p1} /mnt/boot/efi")
else:
    os.system("mkdir /mnt/boot")
    os.system(f"mount /dev/${p1} /mnt/boot")
os.system(f"pacstrap /mnt base linux linux-firmware grub efibootmgr sudo {'xorg plasma kde-applications plasma-wayland-session' if inskde.lower() == 'y' else ''}")
os.system("genfstab -U /mnt >> /mnt/etc/fstab")
os.system("echo 'localhost' > /mnt/etc/hostname")
os.system("echo 'LANG=en_US.UTF-8 >> /mnt/etc/locale.conf'")
os.system("arch-chroot /mnt locale-gen &> /dev/null")
if isuefi: os.system("arch-chroot /mnt grub-install --target=x86_64-efi --efi-directory=/boot/efi")
else: os.system(f"arch-chroot /mnt grub-install /dev/{dev}")
os.system("arch-chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg")
if inskde.lower() == "y":
    os.system("arch-chroot /mnt systemctl enable NetworkManager")
    os.system("arch-chroot /mnt systemctl enable sddm")
username = input("Type a username: ")
os.system(f"arch-chroot /mnt useradd {username} -d /home/{username}")
while True:
    password = input("Type a password (press enter for no password): ")
    if len(password) == 0:
        os.system(f"arch-chroot /mnt passwd -d {username}")
        break
    else:
        pconf = input(f"Confirm password: ")
        if pconf == password:
            os.system(f"echo '{password}\\n{pconf}' | passwd {username}")
            break
        else: print("Passwords do not match")
os.system(f"arch-chroot /mnt usermod -aG wheel {username}")
os.system("echo '%wheel ALL=(ALL) ALL' >> /mnt/etc/sudoers")
os.system("echo '%sudo ALL=(ALL) ALL' >> /mnt/etc/sudoers")
os.system("umount -R /mnt")
print("Rebooting in 5 seconds...")
time.sleep(5)
os.system("reboot")
