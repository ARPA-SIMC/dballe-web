Summary: Graphical interface to DB-All.e databases
Name: provami-qt
Version: 1.0.0
Release: 4831%{dist}
License: GPL
Group: Applications/Meteo
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildRequires: cmake, libdballe-devel, qt5-qtbase-devel, qt5-qtwebkit-devel
Requires: python-dballe, dballe, numpy, rpy
#Obsoletes: provami

%description

 provami is a GUI application to visualise and navigate DB-All.e databases.
 It also allows to perform simple editing tasks, and to graphically select and
 export data subsets.


%prep
%setup -q 

%build

%cmake .

make %{?_smp_mflags}

%install
[ "%{buildroot}" != / ] && rm -rf "%{buildroot}"

make install DESTDIR="%{buildroot}"

%check
ctest -V %{?_smp_mflags}

%clean
[ "%{buildroot}" != / ] && rm -rf "%{buildroot}"

%files
%defattr(-,root,root,-)
%{_datadir}/provami/mapview
%{_bindir}/provami-qt
%doc %{_mandir}/man1/provami-qt.1.gz


%post


%postun

%changelog
* Fri Sep 25 2015 Daniele Branchini <dbranchini@arpa.emr.it> - qt1.0.0-4831%{dist}
- fixed issue https://github.com/ARPA-SIMC/provami/issues/2

* Thu Sep 24 2015 Daniele Branchini <dbranchini@arpa.emr.it> - qt1.0.0-4830%{dist}
- added man page and help options

* Wed Apr 22 2015 Daniele Branchini <dbranchini@arpa.emr.it> - qt1.0.0-4687%{dist}
- rebuild con cmake

* Tue Feb 17 2015 Daniele Branchini <dbranchini@arpa.emr.it> - qt1.0.0-4508%{dist}
- aggiunta gestione summary

* Thu Feb 12 2015 Daniele Branchini <dbranchini@arpa.emr.it> - qt1.0.0-4497%{dist}
- aggiunta una riga che mostra gli estremi di date e il numero di risultati stimati
- aggiunto un secondo bottone per fare refresh ricalcolando anche le statistiche
- fatto in modo che il refresh blocchi l\'interfaccia per il meno tempo possibile

* Thu Feb 5 2015 Daniele Branchini <dbranchini@arpa.emr.it> - qt1.0.0-4479%{dist}
- first build