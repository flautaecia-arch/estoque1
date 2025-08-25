// Configuração da API
const API_BASE = '/api';

// Estado da aplicação
let currentProduct = null;
let produtos = [];
let contagens = [];

// Elementos DOM
const elements = {
    // Tabs
    tabBtns: document.querySelectorAll('.tab-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // Produtos
    novoProdutoBtn: document.getElementById('novoProdutoBtn'),
    produtoForm: document.getElementById('produtoForm'),
    formProduto: document.getElementById('formProduto'),
    cancelarProdutoBtn: document.getElementById('cancelarProdutoBtn'),
    produtosTable: document.getElementById('produtosTable'),
    importarBtn: document.getElementById('importarBtn'),
    templateBtn: document.getElementById('templateBtn'),
    
    // Contagem
    buscaCodigo: document.getElementById('buscaCodigo'),
    buscarProdutoBtn: document.getElementById('buscarProdutoBtn'),
    produtoEncontrado: document.getElementById('produtoEncontrado'),
    produtoInfo: document.getElementById('produtoInfo'),
    formContagem: document.getElementById('formContagem'),
    listaContagens: document.getElementById('listaContagens'),
    
    // Relatórios
    gerarPdfBtn: document.getElementById('gerarPdfBtn'),
    gerarExcelBtn: document.getElementById('gerarExcelBtn'),
    verResumoBtn: document.getElementById('verResumoBtn'),
    novaContagemBtn: document.getElementById('novaContagemBtn'),
    resumoContainer: document.getElementById('resumoContainer'),
    resumoContent: document.getElementById('resumoContent'),
    
    // Modal e Loading
    uploadModal: document.getElementById('uploadModal'),
    uploadForm: document.getElementById('uploadForm'),
    editModal: document.getElementById('editModal'),
    editForm: document.getElementById('editForm'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    toastContainer: document.getElementById('toastContainer'),
    
    // Refresh
    refreshBtn: document.getElementById('refreshBtn')
};

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupEventListeners();
    loadProdutos();
    
    // Ativar primeira tab
    showTab('produtos');
}

function setupEventListeners() {
    // Tabs
    elements.tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            showTab(tabName);
        });
    });
    
    // Produtos
    elements.novoProdutoBtn.addEventListener('click', showProdutoForm);
    elements.cancelarProdutoBtn.addEventListener('click', hideProdutoForm);
    elements.formProduto.addEventListener('submit', handleProdutoSubmit);
    elements.importarBtn.addEventListener('click', showUploadModal);
    elements.templateBtn.addEventListener('click', downloadTemplate);
    
    // Contagem
    elements.buscarProdutoBtn.addEventListener('click', buscarProduto);
    elements.buscaCodigo.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            buscarProduto();
        }
    });
    elements.formContagem.addEventListener('submit', handleContagemSubmit);
    
    // Relatórios
    elements.gerarPdfBtn.addEventListener('click', gerarRelatorioPdf);
    elements.gerarExcelBtn.addEventListener('click', gerarRelatorioExcel);
    elements.verResumoBtn.addEventListener('click', verResumo);
    elements.novaContagemBtn.addEventListener('click', iniciarNovaContagem);
    
    // Modal
    elements.uploadForm.addEventListener('submit', handleUploadSubmit);
    elements.editForm.addEventListener('submit', handleEditSubmit);
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            hideUploadModal();
            hideEditModal();
        });
    });
    
    // Refresh
    elements.refreshBtn.addEventListener('click', refreshData);
    
    // Click fora do modal
    elements.uploadModal.addEventListener('click', (e) => {
        if (e.target === elements.uploadModal) {
            hideUploadModal();
        }
    });
}

// Funções de Tab
function showTab(tabName) {
    // Atualizar botões
    elements.tabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Atualizar conteúdo
    elements.tabContents.forEach(content => {
        content.classList.toggle('active', content.id === tabName);
    });
    
    // Carregar dados específicos da tab
    if (tabName === 'produtos') {
        loadProdutos();
    } else if (tabName === 'contagem') {
        elements.buscaCodigo.focus();
    }
}

// Funções de API
async function apiCall(endpoint, options = {}) {
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || `Erro HTTP: ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('Erro na API:', error);
        showToast(error.message, 'error');
        throw error;
    } finally {
        hideLoading();
    }
}

// Funções de Produtos
async function loadProdutos() {
    try {
        const response = await apiCall('/produtos');
        produtos = response.produtos || [];
        renderProdutosTable();
    } catch (error) {
        console.error('Erro ao carregar produtos:', error);
    }
}

function renderProdutosTable() {
    const tbody = elements.produtosTable.querySelector('tbody');
    
    if (produtos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center">
                    <p>Nenhum produto cadastrado</p>
                    <button class="btn btn-primary mt-2" onclick="showProdutoForm()">
                        <i class="fas fa-plus"></i> Cadastrar Primeiro Produto
                    </button>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = produtos.map(produto => `
        <tr>
            <td><strong>${produto.codigo}</strong></td>
            <td>${produto.nome}</td>
            <td>${formatDate(produto.created_at)}</td>
            <td>
                <button class="btn btn-outline" onclick="editProduto(${produto.id})" title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-danger" onclick="deleteProduto(${produto.id})" title="Excluir">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function showProdutoForm() {
    elements.produtoForm.style.display = 'block';
    elements.produtoForm.scrollIntoView({ behavior: 'smooth' });
    document.getElementById('produtoCodigo').focus();
}

function hideProdutoForm() {
    elements.produtoForm.style.display = 'none';
    elements.formProduto.reset();
}

async function handleProdutoSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        codigo: formData.get('codigo'),
        nome: formData.get('nome')
    };
    
    try {
        await apiCall('/produtos', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        showToast('Produto criado com sucesso!', 'success');
        hideProdutoForm();
        loadProdutos();
    } catch (error) {
        console.error('Erro ao criar produto:', error);
    }
}

async function deleteProduto(id) {
    if (!confirm('Tem certeza que deseja excluir este produto? Todas as contagens serão perdidas.')) {
        return;
    }
    
    try {
        await apiCall(`/produtos/${id}`, {
            method: 'DELETE'
        });
        
        showToast('Produto excluído com sucesso!', 'success');
        loadProdutos();
    } catch (error) {
        console.error('Erro ao excluir produto:', error);
    }
}

// Funções de Contagem
async function buscarProduto() {
    const codigo = elements.buscaCodigo.value.trim();
    
    if (!codigo) {
        showToast('Digite um código de produto', 'warning');
        return;
    }
    
    try {
        const response = await apiCall(`/produtos/${codigo}`);
        currentProduct = response.produto;
        
        showProdutoEncontrado();
        loadContagensProduto(codigo);
        
    } catch (error) {
        elements.produtoEncontrado.style.display = 'none';
        currentProduct = null;
    }
}

function showProdutoEncontrado() {
    if (!currentProduct) return;
    
    elements.produtoInfo.textContent = `${currentProduct.codigo} - ${currentProduct.nome}`;
    elements.produtoEncontrado.style.display = 'block';
    elements.produtoEncontrado.scrollIntoView({ behavior: 'smooth' });
    
    // Limpar formulário
    elements.formContagem.reset();
    document.getElementById('lote').focus();
}

async function loadContagensProduto(codigo) {
    try {
        const response = await apiCall(`/contagens/produto/${codigo}`);
        contagens = response.contagens || [];
        renderContagens();
    } catch (error) {
        console.error('Erro ao carregar contagens:', error);
        contagens = [];
        renderContagens();
    }
}

function renderContagens() {
    if (contagens.length === 0) {
        elements.listaContagens.innerHTML = '<p class="text-center">Nenhuma contagem registrada para este produto.</p>';
        return;
    }
    
    const totalQuantidade = contagens.reduce((sum, c) => sum + c.quantidade, 0);
    
    elements.listaContagens.innerHTML = `
        <div class="mb-2">
            <strong>Total em Estoque: ${totalQuantidade} unidades</strong>
        </div>
        ${contagens.map(contagem => `
            <div class="contagem-item">
                <div class="contagem-info">
                    <strong>Lote: ${contagem.lote}</strong><br>
                    <small>Validade: ${contagem.validade_formatada} | Quantidade: ${contagem.quantidade}</small>
                </div>
                <div class="contagem-actions">
                    <button class="btn btn-outline" onclick="editContagem(${contagem.id})" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-danger" onclick="deleteContagem(${contagem.id})" title="Excluir">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('')}
    `;
}

async function handleContagemSubmit(e) {
    e.preventDefault();
    
    if (!currentProduct) {
        showToast('Nenhum produto selecionado', 'error');
        return;
    }
    
    const formData = new FormData(e.target);
    const data = {
        codigo_produto: currentProduct.codigo,
        lote: formData.get('lote'),
        validade_mes: formData.get('validade_mes'),
        validade_ano: formData.get('validade_ano'),
        quantidade: formData.get('quantidade')
    };
    
    try {
        const response = await apiCall('/contagens', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        // Exibir mensagem detalhada de sucesso
        let toastMessage = `✅ Produto "${response.produto.nome}" (Código: ${response.produto.codigo})\n`;
        if (response.criou_novo) {
            toastMessage += `Lote: ${response.contagem.lote}\nQuantidade adicionada: ${response.contagem.quantidade}\nTotal no lote: ${response.contagem.quantidade}`;
        } else {
            toastMessage += `Lote: ${response.contagem.lote}\nQuantidade adicionada: ${response.quantidade_adicionada}\nQuantidade anterior: ${response.quantidade_anterior}\nNova quantidade total: ${response.contagem.quantidade}`;
        }
        showToast(toastMessage, 'success');
        
        // Limpar formulário
        elements.formContagem.reset();
        document.getElementById('lote').focus();
        
        // Recarregar contagens
        loadContagensProduto(currentProduct.codigo);
        
    } catch (error) {
        console.error('Erro ao registrar contagem:', error);
    }
}

async function deleteContagem(id) {
    if (!confirm('Tem certeza que deseja excluir esta contagem?')) {
        return;
    }
    
    try {
        await apiCall(`/contagens/${id}`, {
            method: 'DELETE'
        });
        
        showToast('Contagem excluída com sucesso!', 'success');
        
        if (currentProduct) {
            loadContagensProduto(currentProduct.codigo);
        }
    } catch (error) {
        console.error('Erro ao excluir contagem:', error);
    }
}

// Funções de Relatórios
async function gerarRelatorioPdf() {
    try {
        showLoading();
        
        const incluirZerados = document.getElementById('filtroRelatorio').value;
        const response = await fetch(`${API_BASE}/relatorio/pdf?incluir_zerados=${incluirZerados}`);
        
        if (!response.ok) {
            throw new Error('Erro ao gerar relatório PDF');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `relatorio_estoque_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        const filtroTexto = incluirZerados === 'true' ? 'todos os itens' : 'apenas itens com estoque';
        showToast(`Relatório PDF gerado com sucesso (${filtroTexto})!`, 'success');
        
    } catch (error) {
        console.error('Erro ao gerar PDF:', error);
        showToast('Erro ao gerar relatório PDF', 'error');
    } finally {
        hideLoading();
    }
}

async function gerarRelatorioExcel() {
    try {
        showLoading();
        
        const incluirZerados = document.getElementById('filtroRelatorio').value;
        const response = await fetch(`${API_BASE}/relatorio/excel?incluir_zerados=${incluirZerados}`);
        
        if (!response.ok) {
            throw new Error('Erro ao gerar relatório Excel');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `relatorio_estoque_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        const filtroTexto = incluirZerados === 'true' ? 'todos os itens' : 'apenas itens com estoque';
        showToast(`Relatório Excel gerado com sucesso (${filtroTexto})!`, 'success');
        
    } catch (error) {
        console.error('Erro ao gerar Excel:', error);
        showToast('Erro ao gerar relatório Excel', 'error');
    } finally {
        hideLoading();
    }
}

async function verResumo() {
    try {
        const incluirZerados = document.getElementById('filtroRelatorio').value;
        const response = await apiCall(`/relatorio/resumo?incluir_zerados=${incluirZerados}`);
        renderResumo(response);
        
        elements.resumoContainer.style.display = 'block';
        elements.resumoContainer.scrollIntoView({ behavior: 'smooth' });
        
        const filtroTexto = incluirZerados === 'true' ? 'todos os itens' : 'apenas itens com estoque';
        showToast(`Resumo carregado (${filtroTexto})`, 'success');
        
    } catch (error) {
        console.error('Erro ao carregar resumo:', error);
    }
}

function renderResumo(data) {
    if (!data.resumo || data.resumo.length === 0) {
        elements.resumoContent.innerHTML = '<p class="text-center">Nenhum dado de estoque encontrado.</p>';
        return;
    }
    
    elements.resumoContent.innerHTML = `
        <div class="resumo-stats mb-3">
            <div class="row">
                <div class="col">
                    <strong>Total de Produtos:</strong> ${data.total_produtos}
                </div>
                <div class="col">
                    <strong>Total Geral:</strong> ${data.total_geral} unidades
                </div>
            </div>
        </div>
        
        ${data.resumo.map(item => `
            <div class="resumo-item">
                <div>
                    <strong>${item.produto.codigo} - ${item.produto.nome}</strong>
                    ${item.contagens.length > 0 ? `
                        <div class="mt-1">
                            ${item.contagens.map(c => 
                                `<small>Lote ${c.lote}: ${c.quantidade} (Val: ${c.validade_formatada})</small>`
                            ).join('<br>')}
                        </div>
                    ` : '<small>Sem estoque</small>'}
                </div>
                <div>
                    <strong>${item.total_quantidade}</strong>
                </div>
            </div>
        `).join('')}
        
        <div class="resumo-item">
            <div><strong>TOTAL GERAL</strong></div>
            <div><strong>${data.total_geral}</strong></div>
        </div>
    `;
}

// Funções de Upload
function showUploadModal() {
    elements.uploadModal.style.display = 'block';
}

function hideUploadModal() {
    elements.uploadModal.style.display = 'none';
    elements.uploadForm.reset();
}

async function handleUploadSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/produtos/importar`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Erro ao importar arquivo');
        }
        
        showToast(data.message, 'success');
        hideUploadModal();
        loadProdutos();
        
        // Mostrar detalhes se houver erros
        if (data.detalhes && data.detalhes.erros.length > 0) {
            console.warn('Erros na importação:', data.detalhes.erros);
            showToast(`${data.detalhes.erros.length} erros encontrados. Verifique o console.`, 'warning');
        }
        
    } catch (error) {
        console.error('Erro no upload:', error);
        showToast(error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function downloadTemplate() {
    try {
        const response = await fetch(`${API_BASE}/produtos/template`);
        
        if (!response.ok) {
            throw new Error('Erro ao baixar template');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'template_produtos.xlsx';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showToast('Template baixado com sucesso!', 'success');
        
    } catch (error) {
        console.error('Erro ao baixar template:', error);
        showToast('Erro ao baixar template', 'error');
    }
}

// Funções de Utilidade
function showLoading() {
    elements.loadingOverlay.style.display = 'block';
}

function hideLoading() {
    elements.loadingOverlay.style.display = 'none';
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    // Converter quebras de linha em <br> para HTML
    const formattedMessage = message.replace(/\n/g, '<br>');
    
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-${getToastIcon(type)}"></i>
            <span>${formattedMessage}</span>
        </div>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    // Auto remove após 8 segundos (mais tempo para mensagens detalhadas)
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 8000);
    
    // Click para remover
    toast.addEventListener('click', () => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    });
}

function getToastIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || icons.info;
}

function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

function refreshData() {
    showToast('Atualizando dados...', 'info');
    
    // Recarregar dados da tab ativa
    const activeTab = document.querySelector('.tab-btn.active').dataset.tab;
    
    if (activeTab === 'produtos') {
        loadProdutos();
    } else if (activeTab === 'contagem' && currentProduct) {
        loadContagensProduto(currentProduct.codigo);
    }
}

// Funções não implementadas (placeholders)
function editProduto(id) {
    showToast('Funcionalidade de edição será implementada em breve', 'info');
}

function editContagem(id) {
    showToast('Funcionalidade de edição será implementada em breve', 'info');
}



// Função para iniciar nova contagem (zerar todas as contagens)
async function iniciarNovaContagem() {
    // Confirmação dupla para evitar exclusões acidentais
    const confirmacao1 = confirm(
        "ATENÇÃO: Esta ação irá ZERAR TODAS as contagens de estoque existentes!\n\n" +
        "Os produtos cadastrados serão mantidos, mas todas as quantidades em estoque serão perdidas.\n\n" +
        "Tem certeza que deseja continuar?"
    );
    
    if (!confirmacao1) {
        return;
    }
    
    const confirmacao2 = confirm(
        "ÚLTIMA CONFIRMAÇÃO:\n\n" +
        "Você está prestes a EXCLUIR TODAS as contagens de estoque.\n" +
        "Esta ação NÃO PODE ser desfeita!\n\n" +
        "Digite 'CONFIRMAR' na próxima caixa de diálogo para prosseguir."
    );
    
    if (!confirmacao2) {
        return;
    }
    
    const textoConfirmacao = prompt(
        "Para confirmar a exclusão de TODAS as contagens, digite exatamente: CONFIRMAR"
    );
    
    if (textoConfirmacao !== "CONFIRMAR") {
        showToast('Operação cancelada. Texto de confirmação incorreto.', 'warning');
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/contagens/zerar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                confirmar: 'SIM_ZERAR_TUDO'
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast(result.message, 'success');
            
            // Limpar dados locais
            contagens = [];
            currentProduct = null;
            
            // Limpar interface
            elements.produtoEncontrado.style.display = 'none';
            elements.buscaCodigo.value = '';
            elements.resumoContainer.style.display = 'none';
            
            // Recarregar dados se estiver na aba de contagem
            const activeTab = document.querySelector('.tab-btn.active').dataset.tab;
            if (activeTab === 'contagem') {
                elements.listaContagens.innerHTML = '<p class="text-muted">Nenhuma contagem encontrada. O estoque foi zerado.</p>';
            }
            
        } else {
            showToast(result.message || 'Erro ao zerar contagens', 'error');
        }
        
    } catch (error) {
        console.error('Erro ao zerar contagens:', error);
        showToast('Erro de conexão ao zerar contagens', 'error');
    } finally {
        hideLoading();
    }
}


// Funções de Edição e Exclusão de Contagens
async function editContagem(contagemId) {
    try {
        showLoading();
        const response = await apiCall(`/contagens/${contagemId}`);
        const contagem = response.contagem;
        
        // Preencher modal de edição
        document.getElementById('editContagemId').value = contagem.id;
        document.getElementById('editProdutoInfo').value = `${contagem.produto.codigo} - ${contagem.produto.nome}`;
        document.getElementById('editLote').value = contagem.lote;
        document.getElementById('editValidadeMes').value = contagem.validade_mes;
        document.getElementById('editValidadeAno').value = contagem.validade_ano;
        document.getElementById('editQuantidade').value = contagem.quantidade;
        
        showEditModal();
        
    } catch (error) {
        console.error('Erro ao carregar contagem para edição:', error);
        showToast('Erro ao carregar dados da contagem', 'error');
    } finally {
        hideLoading();
    }
}

async function deleteContagem(contagemId) {
    if (!confirm('Tem certeza que deseja excluir esta contagem?')) {
        return;
    }
    
    try {
        showLoading();
        await apiCall(`/contagens/${contagemId}`, {
            method: 'DELETE'
        });
        
        showToast('Contagem excluída com sucesso!', 'success');
        
        // Recarregar contagens do produto atual
        if (currentProduct) {
            await loadContagensProduto(currentProduct.codigo);
        }
        
    } catch (error) {
        console.error('Erro ao excluir contagem:', error);
        showToast('Erro ao excluir contagem', 'error');
    } finally {
        hideLoading();
    }
}

async function handleEditSubmit(e) {
    e.preventDefault();
    
    const contagemId = document.getElementById('editContagemId').value;
    const formData = new FormData(e.target);
    
    const data = {
        lote: formData.get('lote'),
        validade_mes: parseInt(formData.get('validade_mes')),
        validade_ano: parseInt(formData.get('validade_ano')),
        quantidade: parseInt(formData.get('quantidade'))
    };
    
    try {
        showLoading();
        await apiCall(`/contagens/${contagemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        showToast('Contagem alterada com sucesso!', 'success');
        hideEditModal();
        
        // Recarregar contagens do produto atual
        if (currentProduct) {
            await loadContagensProduto(currentProduct.codigo);
        }
        
    } catch (error) {
        console.error('Erro ao alterar contagem:', error);
        showToast('Erro ao alterar contagem', 'error');
    } finally {
        hideLoading();
    }
}

// Funções do Modal de Edição
function showEditModal() {
    elements.editModal.style.display = 'flex';
    document.getElementById('editLote').focus();
}

function hideEditModal() {
    elements.editModal.style.display = 'none';
    elements.editForm.reset();
}

