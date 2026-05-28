export const SUPERUSER_ROLES = ['superuser', 'superadmin'];
export const TENANT_ROLES = ['user', 'normal', 'admin', 'admin_empresa'];

export const getUserRole = (user: any): string => (
  user?.tipo_usuario || user?.role || (user?.user_type === 'admin' ? 'superuser' : user?.user_type) || ''
);

export const isSuperUser = (user: any): boolean => (
  SUPERUSER_ROLES.includes(getUserRole(user))
);

export const isTenantUser = (user: any): boolean => (
  TENANT_ROLES.includes(getUserRole(user)) || Boolean(user?.tenant_id)
);

export const getDashboardPath = (user: any): string => {
  if (isSuperUser(user)) {
    return '/super-admin';
  }

  return '/dashboard';
};
