import React from 'react';
import { Layout, Card, Row, Col, Typography, Image, Button, Space } from 'antd';
import { Link } from 'react-router-dom';

const { Header, Content, Footer } = Layout;
const { Title, Paragraph } = Typography;

const HistoryPage: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#1B365D', padding: '0 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ color: 'white', fontSize: '18px' }}>
          Historia de la Guayabera
        </div>
        <Space>
          <Button type="primary" ghost>
            <Link to="/login">Iniciar Sesión</Link>
          </Button>
          <Button type="default" ghost>
            <Link to="/register">Registrarse</Link>
          </Button>
        </Space>
      </Header>
      
      <Content style={{ padding: '20px 40px', marginTop: 20 }}>
        <div style={{ background: '#fff', padding: 24, borderRadius: 8, minHeight: 380 }}>
          <Row gutter={[24, 24]}>
            <Col span={24}>
              <Title level={1} style={{ color: '#1B365D', textAlign: 'center' }}>
                La Historia de la Guayabera
              </Title>
            </Col>
            
            <Col xs={24} md={12}>
              <Card 
                title="Orígenes de la Guayabera" 
                style={{ height: '100%' }}
              >
                <Paragraph>
                  La guayabera, prenda icónica del vestuario masculino cubano y mexicano, tiene orígenes que se remontan al siglo XIX. 
                  Su nombre proviene de "guayaba", fruto tropical abundante en Cuba, ya que inicialmente esta camisa era utilizada 
                  por los campesinos y trabajadores del campo para protegerse del sol mientras recolectaban guayabas.
                </Paragraph>
                
                <Paragraph>
                  Existen varias teorías sobre su origen. Un grupo de historiadores afirma que fue creada en el siglo XVIII en el 
                  estado mexicano de Yucatán, mientras que otros sostienen que nació en Cuba en el siglo XIX. Lo cierto es que 
                  esta prenda fue adoptada rápidamente por su comodidad y funcionalidad en climas cálidos.
                </Paragraph>
              </Card>
            </Col>
            
            <Col xs={24} md={12}>
              <Image 
                src="https://via.placeholder.com/500x400/87CEEB/FFFFFF?text=Guayabera+Tradicional" 
                alt="Guayabera Tradicional"
                style={{ width: '100%', borderRadius: 8 }}
              />
            </Col>
            
            <Col xs={24} md={12}>
              <Image 
                src="https://via.placeholder.com/500x400/98FB98/000000?text=Guayabera+Yucateca" 
                alt="Guayabera Yucateca"
                style={{ width: '100%', borderRadius: 8 }}
              />
            </Col>
            
            <Col xs={24} md={12}>
              <Card title="La Guayabera en Yucatán">
                <Paragraph>
                  En la península de Yucatán, la guayabera tomó especial relevancia a partir del siglo XX. Fue en Mérida donde 
                  esta prenda se refinó y se convirtió en parte fundamental del traje regional masculino. La guayabera yucateca 
                  se distingue por sus característicos bolsillos frontales y pliegues verticales decorativos.
                </Paragraph>
                
                <Paragraph>
                  La influencia maya en los diseños y bordados ha sido notable, especialmente en los modelos artesanales. 
                  Durante las celebraciones como la Vaquería Yucateca y otras festividades regionales, la guayabera se convierte 
                  en un elemento de identidad cultural.
                </Paragraph>
              </Card>
            </Col>
            
            <Col xs={24}>
              <Card title="Hiunic - El Traje Regional de Caballero">
                <Row gutter={[24, 24]}>
                  <Col xs={24} md={8}>
                    <Image 
                      src="https://via.placeholder.com/300x400/F4A460/FFFFFF?text=Traje+Hiunic" 
                      alt="Traje Hiunic"
                      style={{ width: '100%', borderRadius: 8 }}
                    />
                  </Col>
                  
                  <Col xs={24} md={16}>
                    <Paragraph>
                      El <em>hiunic</em> es el traje regional masculino tradicional de Yucatán, que complementa a la guayabera. 
                      Esta indumentaria incluye la guayabera como prenda principal, acompañada de pantalón de algodón blanco, 
                      zapatos de charro yucateco y sombrero de jipijapa. En ocasiones especiales, se añade un chaleco bordado 
                      con hilos de colores que representan motivos mayas.
                    </Paragraph>
                    
                    <Paragraph>
                      El término "hiunic" proviene del idioma maya yucateco, y significa "ropa nueva". Este atuendo representa 
                      la fusión de influencias europeas, africanas e indígenas que caracterizan a la cultura yucateca.
                    </Paragraph>
                  </Col>
                </Row>
              </Card>
            </Col>
            
            <Col xs={24}>
              <Card title="Video: La Elaboración Artesanal de una Guayabera">
                <div style={{ textAlign: 'center', padding: '20px' }}>
                  <div 
                    style={{ 
                      position: 'relative', 
                      paddingBottom: '56.25%', 
                      height: 0, 
                      overflow: 'hidden',
                      maxWidth: '100%',
                      background: '#000',
                      borderRadius: 8
                    }}
                  >
                    <div 
                      style={{ 
                        position: 'absolute', 
                        top: 0, 
                        left: 0, 
                        width: '100%', 
                        height: '100%', 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        color: 'white',
                        fontSize: '24px'
                      }}
                    >
                      [Video Player - Proceso de elaboración de una guayabera tradicional]
                    </div>
                  </div>
                  <Paragraph style={{ marginTop: 16 }}>
                    Video documental sobre el proceso artesanal de confección de una guayabera tradicional, 
                    mostrando los detalles de bordado y las técnicas heredadas de generación en generación.
                  </Paragraph>
                </div>
              </Card>
            </Col>
          </Row>
        </div>
      </Content>
      
      <Footer style={{ textAlign: 'center', background: '#1B365D', color: 'white', padding: '20px 0' }}>
        <Paragraph style={{ color: 'white' }}>
          Guayabera ERP Suite v2.0 ©2026 - Celebrando la tradición y cultura de la península de Yucatán
        </Paragraph>
        <Paragraph style={{ color: '#FF8C42' }}>
          "La guayabera: símbolo de identidad cultural y refinamiento"
        </Paragraph>
      </Footer>
    </Layout>
  );
};

export default HistoryPage;
