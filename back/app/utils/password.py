from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()


#加密
def hashed_password(password:str)->str:
    return password_hash.hash(password)



#解密  返回布尔值
def verify_password(plain_password,hashed_password)->bool:
    return password_hash.verify(plain_password,hashed_password)
