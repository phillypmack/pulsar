# Projeto Clareza - Plataforma de Gestão de Trabalho

Uma aplicação web completa para gestão de projetos e tarefas, inspirada no Asana, desenvolvida com React (frontend) e Flask (backend).

## 🚀 Funcionalidades Principais

### ✅ Implementadas e Testadas
- **Sistema de Autenticação**: Login e registro de usuários com JWT
- **Dashboard**: Interface principal com listagem de projetos
- **Gestão de Projetos**: Criação, visualização e gerenciamento de projetos
- **Gestão de Tarefas**: Criação, edição, conclusão e exclusão de tarefas
- **Workspaces**: Organização de projetos em workspaces
- **Interface Responsiva**: Design moderno e responsivo

### 🎯 Arquitetura Baseada na Documentação
- **Grafo de Trabalho**: Implementação completa dos modelos de dados (User, Workspace, Project, Task)
- **API RESTful**: Endpoints completos para todas as operações CRUD
- **Autenticação JWT**: Sistema seguro de autenticação
- **Banco de Dados**: SQLite com SQLAlchemy ORM

## 🛠️ Tecnologias Utilizadas

### Backend
- **Flask**: Framework web Python
- **SQLAlchemy**: ORM para banco de dados
- **Flask-CORS**: Suporte a CORS
- **PyJWT**: Autenticação JWT
- **SQLite**: Banco de dados

### Frontend
- **React**: Biblioteca JavaScript
- **TypeScript**: Tipagem estática
- **React Router**: Roteamento
- **Axios**: Cliente HTTP
- **CSS3**: Estilização moderna

## 📁 Estrutura do Projeto

```
projeto-clareza/
├── server/
│   └── projeto-clareza-backend/
│       ├── src/
│       │   ├── models/
│       │   │   └── work_graph.py      # Modelos de dados
│       │   ├── routes/
│       │   │   ├── auth.py            # Autenticação
│       │   │   ├── projects.py        # Gestão de projetos
│       │   │   ├── tasks.py           # Gestão de tarefas
│       │   │   ├── workspaces.py      # Gestão de workspaces
│       │   │   └── user.py            # Gestão de usuários
│       │   └── main.py                # Aplicação principal
│       ├── run_server.py              # Servidor de desenvolvimento
│       ├── requirements.txt           # Dependências Python
│       └── venv/                      # Ambiente virtual
└── client/
    ├── src/
    │   ├── components/
    │   │   ├── Auth/                  # Componentes de autenticação
    │   │   ├── Dashboard/             # Dashboard principal
    │   │   └── Projects/              # Componentes de projetos
    │   ├── contexts/                  # Contextos React
    │   ├── services/                  # Serviços de API
    │   └── App.tsx                    # Componente principal
    ├── package.json                   # Dependências Node.js
    └── .env                          # Configurações
```

## 🚀 Como Executar

### Pré-requisitos
- Python 3.11+
- Node.js 20+
- npm ou yarn

### Backend (Flask)
```bash
cd server/projeto-clareza-backend
source venv/bin/activate
pip install -r requirements.txt
python run_server.py
```
O backend estará disponível em: `http://localhost:5001`

### Frontend (React)
```bash
cd client
npm install
npm start
```
O frontend estará disponível em: `http://localhost:3000`

## 📊 Modelos de Dados

### User (Usuário)
- `gid`: ID único
- `name`: Nome do usuário
- `email`: Email (único)
- `photo`: URL da foto (opcional)

### Workspace
- `gid`: ID único
- `name`: Nome do workspace
- `is_organization`: Booleano para organização
- `email_domains`: Domínios de email permitidos

### Project (Projeto)
- `gid`: ID único
- `name`: Nome do projeto
- `workspace_gid`: ID do workspace
- `owner_gid`: ID do proprietário
- `default_view`: Visualização padrão (list, board, calendar, timeline)
- `color`: Cor do projeto
- `privacy_setting`: Configuração de privacidade
- `due_on`: Data de vencimento
- `start_on`: Data de início

### Task (Tarefa)
- `gid`: ID único
- `name`: Nome da tarefa
- `notes`: Descrição detalhada
- `assignee_gid`: ID do responsável
- `completed`: Status de conclusão
- `workspace_gid`: ID do workspace
- `due_on`: Data de vencimento
- `start_on`: Data de início
- `parent_gid`: ID da tarefa pai (para subtarefas)

## 🔗 API Endpoints

### Autenticação
- `POST /api/auth/register` - Registrar usuário
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Obter usuário atual

### Workspaces
- `GET /api/workspaces` - Listar workspaces
- `POST /api/workspaces` - Criar workspace
- `GET /api/workspaces/{id}` - Obter workspace
- `PUT /api/workspaces/{id}` - Atualizar workspace
- `DELETE /api/workspaces/{id}` - Deletar workspace

### Projetos
- `GET /api/projects` - Listar projetos
- `POST /api/projects` - Criar projeto
- `GET /api/projects/{id}` - Obter projeto
- `PUT /api/projects/{id}` - Atualizar projeto
- `DELETE /api/projects/{id}` - Deletar projeto
- `GET /api/projects/{id}/tasks` - Listar tarefas do projeto

### Tarefas
- `GET /api/tasks` - Listar tarefas
- `POST /api/tasks` - Criar tarefa
- `GET /api/tasks/{id}` - Obter tarefa
- `PUT /api/tasks/{id}` - Atualizar tarefa
- `DELETE /api/tasks/{id}` - Deletar tarefa
- `POST /api/tasks/{id}/projects` - Adicionar tarefa ao projeto
- `DELETE /api/tasks/{id}/projects/{project_id}` - Remover tarefa do projeto

## 🎨 Interface do Usuário

### Tela de Login/Registro
- Design moderno com gradiente
- Alternância entre login e registro
- Validação de formulários
- Feedback de erros

### Dashboard
- Header com informações do usuário
- Seletor de workspace
- Listagem de projetos em cards
- Botão para criar novos projetos

### Detalhes do Projeto
- Cabeçalho com informações do projeto
- Barra de progresso visual
- Listagem de tarefas organizadas por status
- Funcionalidade para marcar tarefas como concluídas
- Botão para criar novas tarefas

## ✅ Testes Realizados

1. **Registro de Usuário**: ✅ Funcionando
   - Criação de usuário "João Silva" com email "joao@teste.com"
   - Redirecionamento automático para dashboard

2. **Autenticação**: ✅ Funcionando
   - Login com credenciais válidas
   - Persistência de sessão
   - Proteção de rotas

3. **Backend APIs**: ✅ Funcionando
   - Criação de workspace via API
   - Criação de projeto via API
   - Criação de tarefa via API
   - Todas as APIs retornando dados corretos

4. **Interface de Projeto**: ✅ Funcionando
   - Visualização de detalhes do projeto
   - Contagem de tarefas
   - Barra de progresso
   - Design responsivo

## 🔧 Configurações

### Variáveis de Ambiente
- `REACT_APP_API_URL`: URL da API (padrão: http://localhost:5001/api)
- `JWT_SECRET`: Chave secreta para JWT (backend)

### Portas
- Frontend: 3000
- Backend: 5001

## 📝 Próximos Passos

Para expandir a aplicação, considere implementar:
- Upload de arquivos
- Comentários em tarefas
- Notificações em tempo real
- Relatórios e dashboards
- Integração com calendário
- Aplicativo mobile
- Deploy em produção

## 🤝 Contribuição

Este projeto foi desenvolvido seguindo as especificações da documentação técnica fornecida, implementando uma versão completa e funcional da plataforma de gestão de trabalho.

## 📄 Licença

Projeto desenvolvido para fins educacionais e demonstrativos.

