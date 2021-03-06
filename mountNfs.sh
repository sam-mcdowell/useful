#!/usr/bin/env bash

IFCONFIG="ifconfig utun0"

VPNUP=`$IFCONFIG | grep "UP" | wc -l`;

REMOUNT=true
while getopts n OPTION; do
    case $OPTION in
        n)
            REMOUNT=false
            ;;
    esac
done

NFS_MOUNT_OPTS=resvport,tcp,hard,intr,nosuid,noatime,noatime
SSHFS_MOUNT_OPTS=follow_symlinks,noappledouble,allow_other

if test $VPNUP -gt 0; then
    sudo umount -f /ext/build
    sudo umount -f /ext/home

    if $REMOUNT ; then
        echo "VPN up, mounting via sshfs"
	sudo sshfs -o $SSHFS_MOUNT_OPTS -o volname=build,cache_timeout=3600 $USER@bastion:/ext/build /ext/build
        sudo sshfs -o $SSHFS_MOUNT_OPTS -o volname=home,cache=no,nolocalcaches $USER@bastion:/ext/home /ext/home
    fi
else
    sudo umount -f /ext/build
    sudo umount -f /ext/ldbuild1
    #sudo umount -f /ext/home
    
    if $REMOUNT ; then
        echo "VPN down, mounting directly"
        sudo mount -o $NFS_MOUNT_OPTS -t nfs build:/data/build /ext/build
        sudo mount -o $NFS_MOUNT_OPTS -t nfs build:/data/ldbuild1 /ext/ldbuild1
        sudo mount -o $NFS_MOUNT_OPTS -t nfs -w home:/data/home /ext/home
    fi
fi
