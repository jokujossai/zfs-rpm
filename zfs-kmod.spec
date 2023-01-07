%define module  zfs

%define buildforkernels akmod
%global debug_package %{nil}

Name:           %{module}-kmod

Version:        2.1.9
Release:        1%{?dist}
Summary:        Kernel module(s)

Group:          System Environment/Kernel
License:        CDDL
URL:            https://github.com/openzfs/zfs
#Source0:        %{module}-%{version}.tar.gz
Source0:        https://github.com/openzfs/zfs/releases/download/%{module}-%{version}/%{module}-%{version}.tar.gz

# The developments headers will conflict with the dkms packages.
Conflicts:      %{module}-dkms

%global AkmodsBuildRequires %{_bindir}/kmodtool time elfutils-libelf-devel gcc
BuildRequires:  %{AkmodsBuildRequires}

# LDFLAGS are not sanitized by arch/*/Makefile for these architectures.
%ifarch ppc ppc64 ppc64le aarch64
%global __global_ldflags %{nil}
%endif

# Kmodtool does its magic here.  A patched version of kmodtool is shipped
# with the source rpm until kmod development packages are supported upstream.
# https://bugzilla.rpmfusion.org/show_bug.cgi?id=2714
%{expand:%(kmodtool --target %{_target_cpu} --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?prefix:--prefix "%{?prefix}"} %{?kernels:--for-kernels "%{?kernels}"} %{?kernelbuildroot:--buildroot "%{?kernelbuildroot}"} 2>/dev/null) }


%description
This package contains the ZFS kernel modules.

%prep
kmodtool --target %{_target_cpu} --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?prefix:--prefix "%{?prefix}"} %{?kernels:--for-kernels "%{?kernels}"} %{?kernelbuildroot:--buildroot "%{?kernelbuildroot}"} 2>/dev/null


%setup -T -c
tar -xf %{SOURCE0}
mv %{module}-%{version} %{name}-%{version}
pushd %{name}-%{version}
popd

# Error out if there was something wrong with kmodtool.
%{?kmodtool_check}

%if %{with debug}
    %define debug --enable-debug
%else
    %define debug --disable-debug
%endif

%if %{with debuginfo}
    %define debuginfo --enable-debuginfo
%else
    %define debuginfo --disable-debuginfo
%endif

# Leverage VPATH from configure to avoid making multiple copies.
%define _configure ../%{module}-%{version}/configure

for kernel_version in %{?kernel_versions}; do
    cp -al %{name}-%{version} _kmod_build_${kernel_version%%___*}
done

%build
for kernel_version in %{?kernel_versions}; do
    cd _kmod_build_${kernel_version%%___*}
    ./configure \
        --with-config=kernel \
        --with-linux=${kernel_version##*___} \
        --with-linux-obj=${kernel_version##*___} \
        %{debug} \
        %{debuginfo} \
        %{?kernel_cc} \
        %{?kernel_ld} \
        %{?kernel_llvm}
    make %{?_smp_mflags}
    cd ..
done


%install
# Relies on the kernel 'modules_install' make target.
for kernel_version in %{?kernel_versions}; do
    install -d %{buildroot}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}
    install _kmod_build_${kernel_version%%___*}/module/*/*.ko %{buildroot}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}
#    cd _kmod_build_${kernel_version%%___*}
#    make install \
#        DESTDIR=${RPM_BUILD_ROOT} \
#        %{?prefix:INSTALL_MOD_PATH=%{?prefix}} \
#        INSTALL_MOD_DIR=%{kmodinstdir_postfix}
#    cd ..
done

%{?akmod_install}


%clean
rm -rf $RPM_BUILD_ROOT
