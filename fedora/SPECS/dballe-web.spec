Summary: Graphical interface to DB-All.e databases
Name: dballe-web
Version: 0.1
Release: 1
License: GPL
Group: Applications/Meteo
Source0: https://github.com/arpa-simc/%{name}/archive/v%{version}-%{release}.tar.gz#/%{name}-%{version}-%{release}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot

%if 0%{?rhel} == 7
%define python3_vers python34
%else
%define python3_vers python3
%endif

BuildRequires: %{python3_vers}-devel
Requires: %{python3_vers}-dballe
Requires: %{python3_vers}-tornado
Requires: %{python3_vers}numpy

%description

 dballe-web is a GUI application to visualise and navigate DB-All.e databases.
 It also allows to perform simple editing tasks, and to graphically select and
 export data subsets.

%global debug_package %{nil}

%prep
%setup -q -n %{name}-%{version}-%{release}

%build
%py3_build

%install
[ "%{buildroot}" != / ] && rm -rf "%{buildroot}"
%py3_install

%check

%clean
[ "%{buildroot}" != / ] && rm -rf "%{buildroot}"

%files
%defattr(-,root,root,-)
%{_bindir}/dballe-web
%dir %{python3_sitelib}/dballe_web
%{python3_sitelib}/dballe_web/*
%{python3_sitelib}/dballe_web*egg-info

%post


%postun

%changelog
* Wed Feb 27 2019 Daniele Branchini <dbranchini@arpae.it> - 0.1-1%{dist}
- first build
