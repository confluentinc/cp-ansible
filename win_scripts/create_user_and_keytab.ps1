Param (
    [Parameter(Mandatory=$true)][string]$ad_domain,
    [Parameter(Mandatory=$true)][string]$ldap_root,
    [Parameter(Mandatory=$true)][string]$user_name,
    [Parameter(Mandatory=$true)][string]$upn,
    [string]$extra_spn='',
    [Parameter(Mandatory=$true)][string]$keytab_dir
 )

Write-Host "ad_domain: $ad_domain"
Write-Host "ldap_root: $ldap_root"
Write-Host "user_name: $user_name"
Write-Host "upn: $upn"
Write-Host "extra_spn: $extra_spn"
Write-Host "keytab_dir: $keytab_dir"

Import-Module ActiveDirectory

# Create user
$initialUpn = $user_name + "@" + $ad_domain
Write-Host "Creating user $initialUpn"
New-ADUser `
    -Name:$user_name `
    -OtherAttributes:@{"msDS-SupportedEncryptionTypes"="24"} `
    -Path:$ldap_root `
    -SamAccountName:$user_name `
    -Type:"user" `
    -ChangePasswordAtLogon:$false `
    -PasswordNeverExpires:$true `
    -UserPrincipalName:$initialUpn    

# Generate KeyTab
$keytabFile = $keytab_dir + "\" + $user_name + ".keytab"
Write-Host "Generating keytab $keytabFile with $upn"
ktpass `
    /out $keytabFile `
    /princ $upn `
    /mapuser $user_name `
    /crypto AES256-SHA1 `
    /ptype KRB5_NT_PRINCIPAL `
    /pass "Confluent1!" `
    /target $ad_domain

# Enable user account
$identity = "CN=" + $user_name + "," + $ldap_root
Write-Host "Enabling user account for $identity"
Enable-ADAccount -Identity:$identity

if ([string]::IsNullOrEmpty($extra_spn)) {
    # Add extraSPN
    setspn -S $extra_spn $user_name
}
