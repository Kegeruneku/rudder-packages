#####################################################################################
# Copyright 2011 Normation SAS
#####################################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#####################################################################################

#=================================================
# Specification file for rudder-webapp
#
# Installs Rudder's WAR files
#
# Copyright (C) 2011 Normation
#=================================================

#=================================================
# Variables
#=================================================
%define real_name        rudder-webapp

%define rudderdir        /opt/rudder
%define ruddervardir     /var/rudder
%define rudderlogdir     /var/log/rudder

%define maven_settings settings-external.xml

#=================================================
# Header
#=================================================
Summary: Configuration management and audit tool - webapp
Name: %{real_name}
Version: %{real_version}
Release: 1%{?dist}
Epoch: 1299256513
License: AGPLv3
URL: http://www.rudder-project.org

Group: Applications/System

Source1: rudder-users.xml
Source2: rudder.xml
Source5: rudder-upgrade

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch: noarch

BuildRequires: jdk
Requires: jre rudder-jetty rudder-inventory-ldap rudder-inventory-endpoint rudder-reports rudder-policy-templates apache2 apache2-utils git-core

%description
Rudder is an open source configuration management and audit solution.

This package contains the web application that is the main user interface to
Rudder. The webapp is automatically installed and started using the Jetty
application server bundled in the rudder-jetty package.


#=================================================
# Source preparation
#=================================================
%prep

cp -rf %{_sourcedir}/rudder-sources %{_builddir}

#=================================================
# Building
#=================================================
%build

cd %{_builddir}/rudder-sources/rudder-parent-pom && %{_sourcedir}/maven2/bin/mvn -s %{_sourcedir}/%{maven_settings} -Dmaven.test.skip=true install
cd %{_builddir}/rudder-sources/rudder-commons && %{_sourcedir}/maven2/bin/mvn -s %{_sourcedir}/%{maven_settings} -Dmaven.test.skip=true install
cd %{_builddir}/rudder-sources/scala-ldap && %{_sourcedir}/maven2/bin/mvn -s %{_sourcedir}/%{maven_settings} -Dmaven.test.skip=true install
cd %{_builddir}/rudder-sources/ldap-inventory && %{_sourcedir}/maven2/bin/mvn -s %{_sourcedir}/%{maven_settings} -Dmaven.test.skip=true install
cd %{_builddir}/rudder-sources/cf-clerk && %{_sourcedir}/maven2/bin/mvn -s %{_sourcedir}/%{maven_settings} -Dmaven.test.skip=true install
cd %{_builddir}/rudder-sources/rudder && %{_sourcedir}/maven2/bin/mvn -s %{_sourcedir}/%{maven_settings} -Dmaven.test.skip=true install package

# Installation
#=================================================
%install
rm -rf %{buildroot}

mkdir -p %{buildroot}%{rudderdir}/etc/
mkdir -p %{buildroot}%{rudderdir}/etc/plugins/
mkdir -p %{buildroot}%{rudderdir}/bin/
mkdir -p %{buildroot}%{rudderdir}/jetty7/webapps/
mkdir -p %{buildroot}%{rudderdir}/jetty7/contexts/
mkdir -p %{buildroot}%{rudderdir}/jetty7/rudder-plugins/
mkdir -p %{buildroot}%{rudderdir}/share/tools
mkdir -p %{buildroot}%{rudderdir}/share/plugins/
mkdir -p %{buildroot}%{ruddervardir}/inventories/incoming
mkdir -p %{buildroot}%{ruddervardir}/inventories/received
mkdir -p %{buildroot}%{rudderlogdir}/apache2/
mkdir -p %{buildroot}/etc/apache2/vhosts.d/

cp %{SOURCE1} %{buildroot}%{rudderdir}/etc/
cp %{_sourcedir}/rudder-sources/rudder/rudder-core/src/main/resources/ldap/bootstrap.ldif %{buildroot}%{rudderdir}/share/
cp %{_sourcedir}/rudder-sources/rudder/rudder-core/src/main/resources/ldap/init-policy-server.ldif %{buildroot}%{rudderdir}/share/
cp %{_sourcedir}/rudder-sources/rudder/rudder-core/src/main/resources/ldap/demo-data.ldif %{buildroot}%{rudderdir}/share/
cp %{_sourcedir}/rudder-sources/rudder/rudder-web/src/main/resources/configuration.properties.sample %{buildroot}%{rudderdir}/etc/rudder-web.properties
cp %{_sourcedir}/rudder-sources/rudder/rudder-web/src/main/resources/logback.xml %{buildroot}%{rudderdir}/etc/

cp %{_builddir}/rudder-sources/rudder/rudder-web/target/rudder-web*.war %{buildroot}%{rudderdir}/jetty7/webapps/rudder.war

cp -rf %{_sourcedir}/rudder-sources/rudder/rudder-web/src/main/resources/load-page %{buildroot}%{rudderdir}/share/
cp %{_sourcedir}/rudder-sources/rudder/rudder-core/src/test/resources/script/cfe-red-button.sh %{buildroot}%{rudderdir}/bin/
cp %{_sourcedir}/rudder-sources/rudder/rudder-core/src/main/resources/reportsInfo.xml %{buildroot}%{rudderdir}/etc/
cp %{_sourcedir}/rudder-sources/rudder/rudder-web/src/main/resources/apache2-default.conf %{buildroot}/etc/apache2/vhosts.d/
cp %{SOURCE2} %{buildroot}%{rudderdir}/jetty7/contexts/

cp %{SOURCE5} %{buildroot}%{rudderdir}/bin/

%pre -n rudder-webapp
#=================================================
# Pre Installation
#=================================================

%post -n rudder-webapp
#=================================================
# Post Installation
#=================================================

echo "Setting apache2 as a boot service"
/sbin/chkconfig --add apache2

echo "Reloading syslogd ..."
/etc/init.d/syslog reload

/etc/init.d/apache2 stop
# a2dissite default

# Do this ONLY at first install
if [ $1 -eq 1 ]
then
        echo 'APACHE_MODULES="${APACHE_MODULES} rewrite dav dav_fs proxy proxy_http"' >> /etc/sysconfig/apache2
		echo 'DAVLockDB /tmp/davlock.db' >> /etc/apache2/conf.d/dav_mod.conf

		mkdir -p /var/rudder/configuration-repository
		mkdir -p /var/rudder/configuration-repository/shared-files
		touch /var/rudder/configuration-repository/shared-files/.placeholder
		cp -a /opt/rudder/share/policy-templates /var/rudder/configuration-repository/
fi

chown root:www %{ruddervardir}/inventories/incoming
chmod 2770 %{ruddervardir}/inventories/incoming
chmod 755 -R %{rudderdir}/share/tools
chmod 655 -R %{rudderdir}/share/load-page
htpasswd2 -bc %{rudderdir}/etc/htpasswd-webdav rudder rudder
/etc/init.d/apache2 start

# Run any upgrades
# Note this must happen *before* creating the policy-template store, as it was moved in version 2.3.2
# and creating it manually would break the upgrade logic
/opt/rudder/bin/rudder-upgrade

# Create and populate policy-template store
if [ ! -d /var/rudder/configuration-repository ]; then mkdir -p /var/rudder/configuration-repository; fi
if [ ! -d /var/rudder/configuration-repository/shared-files ]; then mkdir -p /var/rudder/configuration-repository/shared-files; fi
if [ ! -d /var/rudder/configuration-repository/policy-templates ]; then
	cp -a /opt/rudder/share/policy-templates /var/rudder/configuration-repository/
fi



#=================================================
# Cleaning
#=================================================
%clean
rm -rf %{buildroot}

#=================================================
# Files
#=================================================
%files -n rudder-webapp
%defattr(-, root, root, 0755)

%{rudderdir}/etc/
%config(noreplace) %{rudderdir}/etc/rudder-web.properties
%config(noreplace) %{rudderdir}/etc/rudder-users.xml
%{rudderdir}/bin/
%{rudderdir}/jetty7/webapps/
%{rudderdir}/jetty7/rudder-plugins/
%{rudderdir}/jetty7/contexts/rudder.xml
%{rudderdir}/share
%{ruddervardir}/inventories/incoming
%{ruddervardir}/inventories/received
%{rudderlogdir}/apache2/
/etc/apache2/vhosts.d/


#=================================================
# Changelog
#=================================================
%changelog
* Thu Jul 28 2011 - Matthieu CERDA <matthieu.cerda@normation.com> 2.3-alpha4-1
- Initial package
