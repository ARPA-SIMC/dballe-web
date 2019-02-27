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


%prep
%setup -q -n %{name}-%{version}-%{release}

%build
%{python3_vers} setup.py build

%install
[ "%{buildroot}" != / ] && rm -rf "%{buildroot}"

%{python3_vers} setup.py install --skip-build --root %{buildroot}

%check
%{python3_vers} setup.py test

%clean
[ "%{buildroot}" != / ] && rm -rf "%{buildroot}"

%files
%defattr(-,root,root,-)
#{_datadir}/provami/mapview
#{_bindir}/provami-qt
#doc #{_mandir}/man1/provami-qt.1.gz

%post


%postun

%changelog
* Wed Feb 27 2019 Daniele Branchini <dbranchini@arpae.it> - 0.1-1%{dist}
- first build
