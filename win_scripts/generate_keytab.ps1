Import-Module ActiveDirectory

param (
    [Parameter(Mandatory=$true)][string]$realm,
    [Parameter(Mandatory=$true)][string]$ad_domain,
    [Parameter(Mandatory=$true)][string]$ldap_root,
    [Parameter(Mandatory=$true)][string]$user_name,
    [Parameter(Mandatory=$true)][string]$upn,
    [string]$extra_spn='',
    [Parameter(Mandatory=$true)][string]$keytab_dir
 )

Write-Host "realm: $realm"
Write-Host "ad_domain: $ad_domain"
Write-Host "ldap_root: $ldap_root"

# Create user
$userPrincipalName = $user_name + "@" + $ad_domain
Write-Host "Creating user $userPrincipalName"
New-ADUser `
    -Name:$user_name `
    -OtherAttributes:@{"msDS-SupportedEncryptionTypes"="24"} `
    -Path:$ldap_root `
    -SamAccountName:$user_name `
    -Type:"user" `
    -ChangePasswordAtLogon:$false `
    -PasswordNeverExpires:$true `
    -UserPrincipalName:$userPrincipalName    

# Generate KeyTab
$keytabFile = $keytab_dir + $user_name + ".keytab"
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
