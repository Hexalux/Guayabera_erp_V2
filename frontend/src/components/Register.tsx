import React, { useEffect, useState } from 'react';
import { LockOutlined, UserOutlined, MailOutlined } from '@ant-design/icons';
import { Button, Form, Input, message } from 'antd';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { register } from '../services/authService';
import { AppDispatch, RootState } from '../store';
import { clearError } from '../store/authSlice';

const Register: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch<AppDispatch>();
  const { error } = useSelector((state: RootState) => state.auth) as { error: string | null };
  const initialEmail = (location.state as { email?: string } | null)?.email || '';
  const visibleError = initialEmail ? null : error;

  useEffect(() => {
    if (initialEmail) {
      dispatch(clearError());
    }
  }, [dispatch, initialEmail]);

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      await dispatch(
        register({ 
          email: values.email,
          nombre_completo: values.nombre_completo,
          password: '-' // Sending a dummy value to satisfy the function signature
        })
      ).unwrap();
      
      message.success(
        'Registro exitoso. Se ha enviado un enlace de verificación a su correo electrónico. ' +
        'Por favor revise su bandeja de entrada (y la carpeta de correo no deseado si es necesario).'
      );
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err: any) {
      message.error(err.message || 'Error en el registro');
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
      <div style={{ 
        width: '100%', 
        maxWidth: '500px',
        padding: '24px',
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
      }}>
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
          <p>Crear Cuenta</p>
        </div>
        
        <Form
          name="register_form"
          initialValues={ { remember: true, email: initialEmail } }
          onFinish={onFinish}
        >
          <Form.Item
            name="nombre_completo"
            rules={[{ required: true, message: 'Por favor ingrese su nombre completo' }]}
          >
            <Input
              id="nombre-completo-input"
              addonBefore={<UserOutlined />}
              placeholder="Nombre completo"
              onClick={handleClearError}
            />
          </Form.Item>
          
          <Form.Item
            name="email"
            rules={[
              { 
                required: true, 
                message: 'Por favor ingrese su correo electrónico' 
              },
              {
                type: 'email',
                message: 'El correo electrónico ingresado no es válido'
              }
            ]}
          >
            <Input
              id="email-input"
              addonBefore={<MailOutlined />}
              placeholder="Correo electrónico"
              onClick={handleClearError}
            />
          </Form.Item>
          
          {visibleError && (
            <Form.Item>
              <div style={{ color: '#DC3545', textAlign: 'center', marginBottom: 16 }}>{visibleError}</div>
            </Form.Item>
          )}

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              className="register-form-button" 
              block 
              loading={loading}
              style={{ 
                backgroundColor: '#2E8B57', // Verde Empresarial
                borderColor: '#2E8B57'
              }}
            >
              Registrarse
            </Button>
            <div style={{ marginTop: 16, textAlign: 'center' }}>
              ¿Ya tienes una cuenta? <Link to="/login">Inicia sesión aquí</Link>
            </div>
          </Form.Item>
        </Form>
      </div>
    </div>
  );
};

export default Register;
