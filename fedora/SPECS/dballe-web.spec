# Note: define _srcarchivename in Travis build only.
%{!?srcarchivename: %global srcarchivename %{name}-%{version}-%{release}}

Summary: Graphical interface to DB-All.e databases
Name: dballe-web
Version: 0.2
Release: 1
License: GPL
Group: Applications/Meteo
Source0: https://github.com/arpa-simc/%{name}/archive/v%{version}-%{release}.tar.gz#/%{srcarchivename}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot

%if 0%{?rhel} == 7
%define python3_vers python34
%else
%define python3_vers python3
%endif

BuildRequires: %{python3_vers}-devel
BuildRequires: %{python3_vers}-tornado
BuildRequires: %{python3_vers}-dballe
BuildRequires: %{python3_vers}-setuptools
Requires: %{python3_vers}-dballe
Requires: %{python3_vers}-tornado
Requires: %{python3_vers}-numpy

%description

 dballe-web is a GUI application to visualise and navigate DB-All.e databases.
 It also allows to perform simple editing tasks, and to graphically select and
 export data subsets.

%global debug_package %{nil}

%prep
%setup -q -n %{srcarchivename}

%build
%py3_build

%install
[ "%{buildroot}" != / ] && rm -rf "%{buildroot}"
%py3_install

%check
%{python3_vers} setup.py test

%clean
[ "%{buildroot}" != / ] && rm -rf "%{buildroot}"

%files
%defattr(-,root,root,-)
%{_bindir}/dballe-web
%dir %{python3_sitelib}/dballe_web
%{python3_sitelib}/dballe_web/*.py
%dir %{python3_sitelib}/dballe_web/static
%{python3_sitelib}/dballe_web/static/*
%dir %{python3_sitelib}/dballe_web/templates
%{python3_sitelib}/dballe_web/templates/*.html
%{python3_sitelib}/dballe_web-*egg-info
%{python3_sitelib}/dballe_web/__pycache__

%post


%postun

%changelog
* Tue Mar  5 2019 Daniele Branchini <dbranchini@arpae.it> - 0.2-1
- Fixed build on CentOS7 (#4)
- Fixed tests (#6)
- Other bug fixes (#3, #5, #8, #9, #10)

* Mon Mar  4 2019 Emanuele Di Giacomo <edigiacomo@arpae.it> - 0.1-3
- Added missing files (#5)

* Wed Feb 27 2019 Daniele Branchini <dbranchini@arpae.it> - 0.1-1
- first build
