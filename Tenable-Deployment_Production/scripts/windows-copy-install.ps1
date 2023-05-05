net use y: $env:nas_path\CGOAnsible$ /user:$env:mount_username $env:mount_password /persistent:no
Copy "y:\Tenable\NessusAgent-10.3.0-x64.msi" "c:\Temp\tenable\NessusAgent-10.3.0-x64.msi"
c:\\Temp\\tenable\\NessusAgent-10.3.0-x64.msi /R /S
Start-Sleep 300
msiexec.exe /i "C:\temp\tenable\NessusAgent-10.3.0-x64.msi" NESSUS_GROUPS="AgentCheck" NESSUS_SERVER="cloud.tenable.com:443" NESSUS_KEY=9819640248148aef1d21f8d48fe2f70072aa45a016e3604508f2ca45dc77fa71 /qn
Start-Sleep 300