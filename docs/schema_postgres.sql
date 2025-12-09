-- ============================================
-- Script SQL para Criar Tabelas no PostgreSQL
-- ============================================
-- Este script cria as mesmas tabelas que seu código Python faz automaticamente

-- Criar banco de dados (execute no superusuário postgres)
-- CREATE DATABASE siscall;

-- Usar o banco siscall
\c siscall

-- Tabela de Usuários
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR NOT NULL,
    login VARCHAR UNIQUE NOT NULL,
    senha VARCHAR NOT NULL,
    tipo INTEGER NOT NULL,  -- 0 = Comum, 1 = Admin
    setor VARCHAR,
    trocar_senha BOOLEAN DEFAULT FALSE
);

-- Tabela de Chamados
CREATE TABLE chamados (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    suporte_id INTEGER,
    data_abertura VARCHAR,
    data_inicio_atendimento VARCHAR,
    data_fechamento VARCHAR,
    descricao VARCHAR,
    maquina VARCHAR,
    status VARCHAR DEFAULT 'Aberto',
    diagnostico VARCHAR,
    solucao VARCHAR,
    
    -- Chaves estrangeiras (relações)
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (suporte_id) REFERENCES usuarios(id)
);

-- Criar índices para melhorar performance
CREATE INDEX idx_usuarios_login ON usuarios(login);
CREATE INDEX idx_chamados_usuario_id ON chamados(usuario_id);
CREATE INDEX idx_chamados_suporte_id ON chamados(suporte_id);
CREATE INDEX idx_chamados_status ON chamados(status);

-- ============================================
-- Inserir Dados Iniciais
-- ============================================

-- Hashes SHA256 de senhas (gerados via hashlib.sha256 em Python)
-- admin123 → 240be518fabd2724ddb6f04eeb1da5967448d7e1c33c945b5409b52a928bcc5
-- user123 → 8fa902c1de80621cba4d35b64d69d2c70c1efb4527f0f456c768c90a0b19e07

INSERT INTO usuarios (nome, login, senha, tipo, setor, trocar_senha) VALUES 
(
    'Administrador', 
    'admin', 
    '240be518fabd2724ddb6f04eeb1da5967448d7e1c33c945b5409b52a928bcc5',
    1,
    'TI - Infraestrutura',
    FALSE
);

INSERT INTO usuarios (nome, login, senha, tipo, setor, trocar_senha) VALUES 
(
    'Usuário Teste', 
    'user', 
    '8fa902c1de80621cba4d35b64d69d2c70c1efb4527f0f456c768c90a0b19e07',
    0,
    'Comercial',
    FALSE
);

-- ============================================
-- Verificar dados inseridos
-- ============================================

SELECT * FROM usuarios;
SELECT * FROM chamados;

-- ============================================
-- Gerar senha SHA256 (Exemplos)
-- ============================================
-- Para gerar novas senhas em Python:
-- import hashlib
-- hashlib.sha256("sua_senha".encode()).hexdigest()

-- ============================================
-- Queries Úteis
-- ============================================

-- Listar todos os usuários
SELECT id, nome, login, tipo, setor FROM usuarios;

-- Listar todos os chamados com nomes dos usuários
SELECT 
    c.id,
    u.nome AS usuario,
    c.descricao,
    c.status,
    c.data_abertura
FROM chamados c
JOIN usuarios u ON c.usuario_id = u.id
ORDER BY c.data_abertura DESC;

-- Contar chamados por status
SELECT status, COUNT(*) as total FROM chamados GROUP BY status;

-- Contar chamados por setor
SELECT u.setor, COUNT(c.id) as total 
FROM chamados c
JOIN usuarios u ON c.usuario_id = u.id
GROUP BY u.setor;

-- Listar chamados em andamento
SELECT c.id, u.nome, c.descricao, s.nome as atendente
FROM chamados c
JOIN usuarios u ON c.usuario_id = u.id
LEFT JOIN usuarios s ON c.suporte_id = s.id
WHERE c.status = 'Em andamento';

-- ============================================
-- Dicas PostgreSQL
-- ============================================

-- Ver todas as tabelas
\dt

-- Ver estrutura de uma tabela
\d usuarios

-- Ver todos os índices
\di

-- Ver sequências (ID auto-increment)
\ds

-- Limpar/resetar dados
-- DELETE FROM chamados;
-- DELETE FROM usuarios;
-- TRUNCATE chamados CASCADE;
-- TRUNCATE usuarios CASCADE;

-- Resetar sequências
-- ALTER SEQUENCE usuarios_id_seq RESTART WITH 1;
-- ALTER SEQUENCE chamados_id_seq RESTART WITH 1;
