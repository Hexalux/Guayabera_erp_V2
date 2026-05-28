import React, { useState } from 'react';
import { LockOutlined } from '@ant-design/icons';
import { Button, Form as AntdForm, Input as AntdInput, message } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import { confirmRegistration } from '../services/authService';

const CreateAccount: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: any) => {
    if (!token) {
      message.error('Token de verificación no encontrado');
      return;
    }

    setLoading(true);
    try {
      await confirmRegistration(token, values.password);
      message.success('¡Cuenta creada exitosamente!');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (error: any) {
      message.error(error.message || 'Error al crear la cuenta');
    } finally {
      setLoading(false);
    }
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
          <p>Establecer contraseña</p>
        </div>
        
        <AntdForm 
          name="create_account_form" 
          onFinish={onFinish}
          layout="vertical"
        >
          <AntdForm.Item
            name="password"
            label="Nueva Contraseña"
            rules={[{ required: true, message: 'Por favor ingrese su contraseña' }]}
          >
            <AntdInput.Password
              id="password-input"
              placeholder="Contraseña"
            />
          </AntdForm.Item>
          
          <AntdForm.Item
            name="confirm"
            label="Confirmar Contraseña"
            dependencies={['password']}
            rules={[
              { required: true, message: 'Por favor confirme su contraseña' },
              ({ getFieldValue }: { getFieldValue: any }) => ({
                validator(_: any, value: any) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Las contraseñas no coinciden'));
                },
              }),
            ]}
          >
            <AntdInput.Password
              id="confirm-password-input"
              placeholder="Confirma tu contraseña"
            />
          </AntdForm.Item>
          
          <AntdForm.Item>
            <Button
              type="primary"
              htmlType="submit"
              block
              loading={loading}
              style={{ 
                backgroundColor: '#2E8B57', // Verde Empresarial
                borderColor: '#2E8B57'
              }}
            >
              Crear Cuenta
            </Button>
          </AntdForm.Item>
        </AntdForm>
      </div>
    </div>
  );
};

export default CreateAccount;