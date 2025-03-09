#!/bin/bash

echo "-----------------------------------------"
echo "Finding Vulnerable SUID's"
find / -perm -4000 -type f 2>/dev/null

echo "-----------------------------------------"

echo "Checking for Writable Directories in PATH"
echo $PATH | tr ':' '\n' | xargs -I {} find {} -writable 2>/dev/null

echo "-----------------------------------------"

echo "Checking for Kernel Versions"
uname -r

echo "-----------------------------------------"

echo "Checking /etc/passwd for Possible Users"
cat /etc/passwd

echo "-----------------------------------------"

echo "Looking for Networks"
cat /etc/hosts

echo "-----------------------------------------"

echo "Enumerating /etc"
ls -lah /etc | grep -E 'crontab|cron.d|cron.daily|cron.hourly|cron.weekly|cron.monthly|hosts.allow|hosts.deny|ssh|netconfig'

echo "-----------------------------------------"

echo "Investigating Sockets"
ss -tulpn

echo "-----------------------------------------"

echo "Accessing Shell History"

if [ "$SHELL" == "/usr/bin/zsh" ]; then

    cat ~/.zsh_history

else

    cat ~/.bash_history

fi

echo "-----------------------------------------"

echo "Checking IP Tables"
ls -lah /sbin/iptables

echo "-----------------------------------------"

echo "Listing Tools of Interest on System"
whereis nmap
whereis john
whereis ssh
whereis msfconsole
whereis tcpdump
whereis yara
whereis curl
whereis wget
whereis git
whereis rkhunter
whereis chrootkit
whereis docker
whereis cp
whereis openssl
whereis tor
whereis ufw
whereis java
whereis gcc
whereis g++
whereis python
whereis python2
whereis python3
whereis rust
whereis ruby
whereis perl
whereis 7zip
whereis unzip
whereis gzip
whereis tar
whereis wireshark
whereis tshark
whereis mail

echo "-----------------------------------------"

echo "Enumerating Additional Users"
cat /etc/passwd | grep user
cat /etc/passwd | grep root
cat /etc/passwd | grep admin
cat /etc/passwd | grep administrator
cat /etc/passwd | grep blueteam
cat /etc/passwd | grep sysadmin
cat /etc/passwd | grep networkadmin
cat /etc/passwd | grep soc
cat /etc/passwd | grep ciso
cat /etc/passwd | grep analyst
cat /etc/passwd | grep resonder
cat /etc/passwd | grep director
cat /etc/passwd | grep siem
cat /etc/passwd | grep engineer

echo "-----------------------------------------"

echo "Tracing Real IP"
curl ifconfig.so

echo

echo "-----------------------------------------"

echo "Do You Have a Root Password? [y / n]"
read answer

if [ "$answer" == "y" ]; then

	echo "Please Type Root Password"
	read -s rootpw

	echo "OPENING SHADOW FILE"
	echo "$rootpw" | sudo -S cat /etc/shadow
	echo "-----------------------------------------"
	echo "LISTING /ROOT CONTENTS"
	echo "$rootpw" | sudo -S ls /root

else
	echo "Find a way to Root!"

fi

echo "-----------------------------------------"

found_tools=""

if whereis nmap | grep -q 'nmap'; then
	found_tools+="nmap, "
fi

if whereis john | grep -q 'john'; then
	found_tools+="john, "
fi

if whereis msfconsole | grep -q 'msfconsole'; then
        found_tools+="msfconsole, "
fi

if whereis tcpdump | grep -q 'tcpdump'; then
        found_tools+="tcpdump, "
fi

if whereis tshark | grep -q 'tshark'; then
        found_tools+="tshark, "
fi

if whereis wireshark | grep -q 'wireshark'; then
        found_tools+="wireshark, "
fi

if whereis docker | grep -q 'docker'; then
        found_tools+="docker, "
fi

if whereis python3 | grep -q 'python3'; then
        found_tools+="python3, "
fi

if whereis tor | grep -q 'tor'; then
        found_tools+="tor, "
fi

if [ -n "$found_tools" ]; then

	echo "Attack Vectors Found: $found_tools"
	echo "Use Vectors to Attack & Pivot"
else

	echo "No Attack Vectors Found"

fi

echo "-----------------------------------------"

echo "Do You Want to Remove Tracks?"

read response

if [ "$response" == "y" ]; then

	echo "Beginning Anti-Forensics"
	if [ "$SHELL" == "/usr/bin/zsh" ]; then
		shred -u ~/.zsh_history

	else

		shred -u ~/.bash_history

	fi

else

	echo "Removing Tracks is Recommended"

fi

echo "-----------------------------------------"

echo "Thanks for Using Basher!"
