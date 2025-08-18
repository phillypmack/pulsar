# Projeto Clareza - Plataforma de Gestão de Trabalho Avançada

Uma aplicação web completa de gestão de projetos e tarefas inspirada no Asana, com funcionalidades avançadas de colaboração em tempo real, automação e visualização de dados.

## 🚀 Funcionalidades Principais

### **Gestão de Projetos e Tarefas**
- ✅ **Workspaces e Projetos** organizados hierarquicamente
- ✅ **Tarefas com subtarefas** e relacionamentos complexos
- ✅ **Sistema de dependências** com detecção de ciclos
- ✅ **Seções personalizáveis** para organização
- ✅ **Campos personalizados** (text, number, enum, multi_enum, date)
- ✅ **Atribuição e prazos** com notificações automáticas

### **Colaboração em Tempo Real**
- ✅ **WebSockets** para atualizações instantâneas
- ✅ **Indicadores de digitação** em tempo real
- ✅ **Presença de usuários** por projeto/workspace
- ✅ **Sincronização automática** entre dispositivos
- ✅ **Notificações push** para mudanças importantes

### **Automação Inteligente**
- ✅ **Motor de regras** configurável
- ✅ **7 tipos de triggers** (criação, conclusão, atribuição, etc.)
- ✅ **7 tipos de ações** (mover seção, atribuir, notificar, etc.)
- ✅ **Templates predefinidos** para regras comuns
- ✅ **Modo de teste** para validação de regras
- ✅ **Processamento assíncrono** com Celery

### **Visualização Avançada**
- ✅ **Gráfico Gantt interativo** com dependências
- ✅ **3 modos de visualização** (dias, semanas, meses)
- ✅ **Barras de progresso** por tarefa
- ✅ **Timeline do projeto** com marcos
- ✅ **Dashboard com estatísticas** em tempo real

### **Feed de Atividades**
- ✅ **Timeline completa** de todas as ações
- ✅ **Filtros avançados** por usuário, projeto, tipo
- ✅ **Estatísticas de atividade** com gráficos
- ✅ **Resumos personalizados** e relatórios
- ✅ **Auditoria completa** do sistema

## 🏗️ Arquitetura Técnica

### **Backend (Flask + PostgreSQL)**
```
├── src/
│   ├── models/enhanced_work_graph.py    # Modelos de dados avançados
│   ├── routes/                          # Endpoints REST
│   │   ├── enhanced_tasks.py           # Tarefas com dependências
│   │   ├── custom_fields.py            # Campos personalizados
│   │   ├── automation_rules.py         # Motor de automação
│   │   ├── activity_feed.py            # Feed de atividades
│   │   └── sections.py                 # Gerenciamento de seções
│   ├── tasks/                          # Processamento assíncrono
│   │   ├── automation_tasks.py         # Execução de regras
│   │   └── notification_tasks.py       # Sistema de notificações
│   ├── websocket/                      # Colaboração tempo real
│   │   └── events.py                   # Eventos WebSocket
│   ├── config.py                       # Configurações
│   └── enhanced_main.py                # Aplicação principal
```

### **Frontend (React + TypeScript)**
```
├── src/
│   ├── components/
│   │   ├── Timeline/                   # Visualização Gantt
│   │   │   ├── GanttChart.tsx         # Gráfico interativo
│   │   │   └── TimelineView.tsx       # Visão completa
│   │   ├── Common/                     # Componentes compartilhados
│   │   │   ├── ConnectionStatus.tsx   # Status WebSocket
│   │   │   └── TypingIndicator.tsx    # Indicadores de digitação
│   │   └── [outros componentes...]
│   ├── services/
│   │   ├── websocket.ts               # Cliente WebSocket
│   │   └── api.ts                     # Cliente REST
│   ├── hooks/
│   │   └── useWebSocket.ts            # Hooks para tempo real
│   └── contexts/                       # Contextos React
```

### **Infraestrutura**
- **PostgreSQL** - Banco de dados principal
- **Redis** - Cache e message broker
- **Celery** - Processamento assíncrono
- **Flask-SocketIO** - WebSockets
- **Docker** - Containerização (preparado)

## 🚀 Como Executar

### **Pré-requisitos**
- Python 3.11+
- Node.js 20+
- PostgreSQL 12+
- Redis 6+

### **Backend**
```bash
cd server/projeto-clareza-backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar banco PostgreSQL
sudo -u postgres psql -c "CREATE USER clareza WITH PASSWORD 'Shark5H4RK';"
sudo -u postgres psql -c "CREATE DATABASE clareza OWNER clareza;"

# Executar aplicação
python src/enhanced_main.py
```

### **Frontend**
```bash
cd client

# Instalar dependências
npm install

# Executar aplicação
npm start
```

### **Serviços Auxiliares**
```bash
# Redis (Ubuntu/Debian)
sudo apt install redis-server
sudo systemctl start redis-server

# Celery Worker (terminal separado)
cd server/projeto-clareza-backend
source venv/bin/activate
celery -A src.celery_app worker --loglevel=info

# Celery Beat (agendador - terminal separado)
celery -A src.celery_app beat --loglevel=info
```

## 📊 Endpoints da API

### **Tarefas Avançadas**
- `GET /api/tasks` - Busca com filtros avançados
- `POST /api/tasks` - Criação com dependências e campos personalizados
- `PUT /api/tasks/{id}` - Atualização completa
- `POST /api/tasks/{id}/dependencies` - Gerenciar dependências
- `GET /api/tasks/{id}/blocked-tasks` - Tarefas bloqueadas

### **Campos Personalizados**
- `GET /api/custom-fields` - Listar campos por workspace
- `POST /api/custom-fields` - Criar campo personalizado
- `POST /api/custom-field-values` - Definir valores

### **Automação**
- `GET /api/automation-rules` - Listar regras
- `POST /api/automation-rules` - Criar regra
- `GET /api/automation-rules/templates` - Templates predefinidos
- `POST /api/automation-rules/test/{id}` - Testar regra

### **Feed de Atividades**
- `GET /api/activity-feed` - Feed com filtros
- `GET /api/activity-feed/stats` - Estatísticas
- `GET /api/activity-feed/project-timeline` - Timeline do projeto

### **Seções**
- `GET /api/sections` - Listar seções
- `POST /api/sections/{id}/move-tasks` - Mover tarefas em lote
- `POST /api/sections/reorder` - Reordenar seções

## 🔄 Eventos WebSocket

### **Conexão e Salas**
- `connect` - Estabelecer conexão autenticada
- `join_project` - Entrar em sala de projeto
- `join_workspace` - Entrar em sala de workspace

### **Colaboração**
- `task_update` - Atualização de tarefa em tempo real
- `typing_indicator` - Indicador de digitação
- `user_joined_project` - Presença de usuários

## 🎯 Casos de Uso Avançados

### **1. Automação de Fluxo de Trabalho**
```javascript
// Exemplo: Regra para mover tarefas concluídas
{
  "name": "Mover Concluídas para Done",
  "trigger_type": "task_completed",
  "action_type": "move_to_section",
  "action_parameters": {
    "section_name": "Concluído"
  }
}
```

### **2. Campos Personalizados**
```javascript
// Exemplo: Campo de prioridade
{
  "name": "Prioridade",
  "type": "enum",
  "enum_options": ["Baixa", "Média", "Alta", "Crítica"]
}
```

### **3. Dependências de Tarefas**
```javascript
// Exemplo: Tarefa com dependências
{
  "name": "Implementar Feature X",
  "dependency_gids": ["task-design-id", "task-approval-id"],
  "start_on": "2025-08-20",
  "due_on": "2025-08-30"
}
```

## 📈 Métricas e Monitoramento

### **Health Check**
- `GET /health` - Status dos serviços (banco, Redis)

### **Estatísticas em Tempo Real**
- Progresso de projetos
- Atividade de usuários
- Performance de automação
- Métricas de colaboração

## 🔐 Segurança

- ✅ **Autenticação JWT** para API e WebSockets
- ✅ **Validação de permissões** em tempo real
- ✅ **Sanitização de dados** de entrada
- ✅ **CORS configurado** adequadamente
- ✅ **Rate limiting** básico implementado

## 📱 Responsividade

- ✅ **Design mobile-first**
- ✅ **Gráfico Gantt responsivo**
- ✅ **Touch gestures** para dispositivos móveis
- ✅ **Breakpoints otimizados** para todas as telas

## 🚀 Próximas Funcionalidades

### **Em Desenvolvimento**
- [ ] Relatórios avançados com exportação
- [ ] Integrações com Slack/Teams
- [ ] Templates de projeto
- [ ] Gestão de recursos e capacidade

### **Roadmap**
- [ ] Dashboard executivo
- [ ] Análise de burndown
- [ ] Portfólio de projetos
- [ ] Aprovações e workflows

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 📞 Suporte

Para suporte e dúvidas:
- 📧 Email: suporte@projeto-clareza.com
- 💬 Discord: [Servidor do Projeto](https://discord.gg/projeto-clareza)
- 📖 Documentação: [docs.projeto-clareza.com](https://docs.projeto-clareza.com)

---

**Desenvolvido com ❤️ pela equipe Projeto Clareza**

*Transformando a gestão de trabalho com tecnologia avançada e colaboração em tempo real.*

