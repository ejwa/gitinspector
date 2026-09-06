Name:           gitinspector
Version:        %{version}
Release:        1%{?dist}
Summary:        A statistical analysis tool for git repositories
License:        GPL-3.0-or-later
URL:            https://github.com/ejwa/gitinspector
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
Requires:       git-core

%description
gitinspector is a statistical analysis tool for git repositories. The default
analysis shows general statistics per author, which can be complemented with a
timeline analysis that shows the workload and activity of each author. Under
normal operation, it filters the results to only show statistics about a number
of given extensions and by default only includes source files in the
statistical analysis.

Several output formats are supported, including plain text, HTML, JSON and XML.

%prep
%autosetup

%build
%py3_build

%install
%py3_install
install -D -p -m 0644 docs/gitinspector.1 %{buildroot}%{_mandir}/man1/gitinspector.1

%files
%license LICENSE.txt
%doc README.md CHANGES.txt
%{_bindir}/gitinspector
%{python3_sitelib}/gitinspector/
%{python3_sitelib}/gitinspector-*.egg-info/
%{_mandir}/man1/gitinspector.1*

%changelog
* Sun Sep 06 2026 Ejwa Hosting AB <gitinspector@ejwa.se>
- Packaged from the release tarball; see CHANGES.txt for the changes themselves.
