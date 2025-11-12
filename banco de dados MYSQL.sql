create database servico_auth
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

use servico_auth;

create table users(
id INT AUTO_INCREMENT PRIMARY KEY,
username VARCHAR(100) UNIQUE NOT NULL,
password_hash VARCHAR(255) NOT NULL,
email VARCHAR(255) UNIQUE NOT NULL,
cpf VARCHAR(14) UNIQUE NOT NULL,
data_nascimento DATE NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
last_login TIMESTAMP NULL,
is_active BOOLEAN DEFAULT TRUE,
INDEX idx_username (username),
INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

drop table usuarios;