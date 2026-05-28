import React, { useState } from 'react';
import { LockOutlined, UserOutlined } from '@ant-design/icons';
import { Button, Checkbox, Form as AntdForm, Input as AntdInput, Card, message } from 'antd';
import { useNavigate, Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { login } from '../services/authService';
import { AppDispatch, RootState } from '../store';
import { clearError } from '../store/authSlice';
import { getDashboardPath } from '../utils/authRouting';

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();
  const { error } = useSelector((state: RootState) => state.auth) as { error: string | null };

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      const result = await dispatch(login({ email: values.username, password: values.password })).unwrap();
      message.success('Inicio de sesión exitoso');
      navigate(getDashboardPath(result.user), { replace: true });
    } catch (error: any) {
      const errorMessage = error?.message || error || 'Error en el inicio de sesión';

      if (error?.status === 404 || error?.code === 'EMAIL_NOT_FOUND') {
        dispatch(clearError());
        message.info('Correo no registrado. Crea una cuenta para continuar.');
        navigate('/register', {
          replace: true,
          state: { email: values.username },
        });
        return;
      }

      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleClearError = () => {
    dispatch(clearError());
  };

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center', 
      minHeight: '100vh',
      backgroundColor: '#F5F7FA' // Gris Noble
    }}>
      <Card 
        style={{ 
          width: '100%', 
          maxWidth: '500px',
          padding: '24px',
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{ 
            backgroundColor: '#1B365D', // Azul Profundo
            width: '60px',
            height: '60px',
            borderRadius: '50%',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '16px'
          }}>
            <LockOutlined style={{ fontSize: '24px', color: 'white' }} />
          </div>
          <h2 style={{ color: '#1B365D', marginBottom: 8 }}>Guayabera ERP</h2>
          <p>Iniciar Sesión</p>
        </div>
        
        <AntdForm
          name="login_form"
          initialValues={ { remember: true } }
          onFinish={onFinish}
        >
          <AntdForm.Item
            name="username"
            rules={[{ required: true, message: 'Por favor ingrese su correo electrónico' }]}
          >
            <AntdInput
              id="username-input"
              prefix={<UserOutlined />}
              placeholder="Correo electrónico"
              onClick={handleClearError}
            />
          </AntdForm.Item>
          
          <AntdForm.Item
            name="password"
            rules={[{ required: true, message: 'Por favor ingrese su contraseña' }]}
          >
            <AntdInput
              id="password-input"
              prefix={<LockOutlined />}
              type="password"
              placeholder="Contraseña"
              onClick={handleClearError}
            />
          </AntdForm.Item>
          
          <AntdForm.Item>
            <AntdForm.Item name="remember" valuePropName="checked" noStyle>
              <Checkbox>Recordarme</Checkbox>
            </AntdForm.Item>
            
            <Link to="/recover-password" style={{ float: 'right' }}>
              ¿Olvidó su contraseña?
            </Link>
          </AntdForm.Item>
          
          {error && (
            <AntdForm.Item>
              <div style={{ color: '#DC3545', textAlign: 'center', marginBottom: 16 }}>{error}</div>
            </AntdForm.Item>
          )}

          <AntdForm.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              className="login-form-button" 
              block 
              loading={loading}
              style={{ 
                backgroundColor: '#2E8B57', // Verde Empresarial
                borderColor: '#2E8B57'
              }}
            >
              Iniciar sesión
            </Button>
            <div style={{ marginTop: 16, textAlign: 'center' }}>
              ¿No tienes una cuenta? <Link to="/register">Regístrate aquí</Link>
            </div>
          </AntdForm.Item>
        </AntdForm>
      </Card>
    </div>
  );
};

export default Login;
