$ErrorActionPreference = 'Stop'

Write-Host "Preparando contexto compartilhado para o Gemini..." -ForegroundColor Cyan
Write-Host "Esta rotina e somente leitura: nao altera arquivos, Git ou banco." -ForegroundColor Yellow

$arquivos = @(
    "PROTOCOLO_COLABORACAO_IA.md",
    "PROPOSTA_ESTRATEGIA_EQUIPE_IA.md",
    "GEMINI.md",
    ".github\copilot-instructions.md",
    ".agents\AGENTS.md",
    ".agents\rules\CONTEXTO_ARGUS.md",
    ".agents\rules\BACKUP_NAMING.md",
    ".agents\CATALOGO_COMANDOS.md",
    ".agents\skills\github-bom-dia\SKILL.md",
    ".agents\skills\github-salvar\SKILL.md",
    ".agents\skills\github-ate-amanha\SKILL.md",
    "diario_de_bordo.md"
)

$ausentes = @()
foreach ($arquivo in $arquivos) {
    if (Test-Path $arquivo -PathType Leaf) {
        Write-Host "[OK] $arquivo" -ForegroundColor Green
    } else {
        $ausentes += $arquivo
        Write-Host "[AUSENTE] $arquivo" -ForegroundColor Red
    }
}

if ($ausentes.Count -gt 0) {
    throw "Nao foi possivel preparar o contexto. Arquivo(s) ausente(s): $($ausentes -join ', ')"
}

Write-Host ""
Write-Host "Instrucao para o Gemini:" -ForegroundColor Cyan
Write-Host "Leia integralmente os arquivos listados acima, comece por PROPOSTA_ESTRATEGIA_EQUIPE_IA.md e responda as perguntas dirigidas ao Antigravity-Gemini."
Write-Host "Nao implemente alteracoes ainda. Apresente sua analise, corrija a proposta se necessario e aguarde a aprovacao do usuario."
