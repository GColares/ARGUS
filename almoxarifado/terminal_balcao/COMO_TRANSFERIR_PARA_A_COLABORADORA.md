# Manual Operacional & Guia de Transferência para a Máquina da Colaboradora

**Sistema:** Terminal de Balcão do Almoxarifado (ARGUS Mobile App)  
**Diretório:** `C:\ARGUS\almoxarifado\terminal_balcao\`  
**Atalho na Área de Trabalho:** `Almoxarifado IFAM.lnk`  
**Escopo Estrito:** Materiais de Consumo e Ferramentas (sem equipamentos permanentes de TI).

---

## 1. As 4 Etapas Canônicas de Operação no Balcão

O aplicativo foi projetado no padrão visual de **Mobile Totem** (focado no operador do balcão, dispensando manipulação de planilhas complexas):

### 📥 1. Entradas (Recebimento de Compras / NFs / Doações)
* **Conversão Automática de Embalagens:** Ao registrar uma entrada de Nota Fiscal (ex: 2 Rolos de cabo de 100m ou 2 Latas de 18L), o operador escolhe se dá entrada na embalagem comercial ou em metros/litros. O sistema credita automaticamente o saldo na unidade base de estoque (+200 metros, +36 litros).
* **Histórico Imediato:** Lista cronológica das últimas entradas registradas com data, NF, fornecedor e projeto.

### 📤 2. Saídas & Gestão de Sobras / Ferramentas
* **📦 Consumo Imediato:** Baixa de materiais com destinação a ambientes e projetos. Se for retirada uma lata nova de tinta/líquido, o operador pode marcar a opção `[x] Abrir nova lata`, emitindo na hora a **Etiqueta Adesiva Lateral com Régua de Nível e Validade PAO** e gerando o Recibo de Saída oficial em PDF.
* **🛠️ Empréstimo de Ferramentas:** Controle de retirada de furadeiras, marretas, alicates, etc., com previsão de retorno e emissão do **Termo de Cautela em PDF**.
* **↩️ Devoluções de Ferramentas:** Vistoria rápida de retorno com 1 clique (*"🟢 Em perfeito estado"* vs *"🔴 Com avaria/quebra"*), recompondo o saldo automaticamente.
* **🥫 Retorno de Sobras Fracionadas (Latas & Cabos):** Quando sobra material da obra, o operador clica na lata aberta ou seleciona o material e marca com 1 clique na régua tátil o nível retornado:
  * `[ 75% | 3/4 ]`
  * `[ 50% | 1/2 ]`
  * `[ 25% | 1/4 ]`
  * `[ 0% | Esgotada ]`
  O sistema credita exatamente o volume correspondente de volta ao estoque (ex: 11,25 L), mantendo a contabilidade perfeita. Para sobras de cabos, digita-se os metros devolvidos ao rolo.

### 📊 3. Saldos & Extratos
* **Endereçamento WMS 3D:** Cada material exibe sua localização exata no galpão (`Ambiente > Estrutura/Estante > Posição/Prateleira`).
* **Impressão Rápida de Etiquetas:**
  * `🏷️ WMS`: Gera a etiqueta de prateleira em PDF para colar na estante/gaveteiro.
  * `🥫 Lata`: Gera a etiqueta lateral adesiva com a régua de nível das 4 faixas graduadas e validade PAO para colar na lata de tinta.
* **Extrato Cronológico:** Visão consolidada de todas as entradas e saídas em ordem de ocorrência.

### ⚙️ 4. Gerenciar (CRUD Completo & Legado)
* **Catálogo de Materiais:** Permite cadastrar novos materiais ou editar os 90 itens legados (incluindo Código CATMAT, PDM Nome Básico/Modificador, Unidade Base, Embalagem, Fator de Conversão, Endereço 3D e Validade PAO).
* **Parâmetros do Sistema:** Gerenciamento simples de Solicitantes, Projetos Financiadores, Ambientes e Estruturas físicas.

---

## 2. Encerramento do Expediente Diário

No rodapé da interface, o botão:
☁️ **`[ ENCERRAR O DIA & SALVAR NO DRIVE ]`**
1. Atualiza a planilha Excel mestre oficial: `planilhas_consolidadas/Almoxarifado_ARGUS_Consolidado.xlsx` com 5 abas relacionais formatadas no Padrão Almoxarifado.
2. Gera uma cópia de backup com data: `backups_drive/Backup_Almoxarifado_AAAA-MM-DD.xlsx`.
3. Se configurada a pasta do Google Drive na máquina da colaboradora, envia a cópia instantaneamente para a nuvem.

---

## 3. Como Transferir para o Computador da Colaboradora

1. **Copiar a pasta:** Copie `C:\ARGUS\almoxarifado\terminal_balcao\` para um pendrive ou pasta sincronizada;
2. **Colar no computador dela:** Cole em `C:\ARGUS\almoxarifado\terminal_balcao\` (ou qualquer pasta desejada);
3. **Criar o atalho de 1 clique:**
   * Clique com o botão direito no arquivo `criar_atalho_desktop.ps1` e selecione **"Executar com o PowerShell"** (ou crie um atalho para `iniciar_silencioso.vbs` e coloque o nome "Almoxarifado IFAM");
4. **Configurar o Drive dela (1 única vez):**
   * Abra o aplicativo pelo atalho na Área de Trabalho;
   * No rodapé, clique em **⚙️ Configurações**;
   * Informe a pasta local do Google Drive instalada na máquina dela (ex: `G:\Meu Drive\Almoxarifado`);
   * Clique em **Salvar Configuração**.
