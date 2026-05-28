from passlib.context import CryptContext

# Configuración para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica que la contraseña proporcionada coincida con el hash almacenado
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Genera un hash para la contraseña proporcionada
    """
    return pwd_context.hash(password)