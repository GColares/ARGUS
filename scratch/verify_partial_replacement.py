import os
import openpyxl

base_dir = r"C:\Projetos\ARGUS\gestao_projetos\execucao_financeira"
fin_file = os.path.join(base_dir, "execucao_financeira.xlsx")
conv_dir = os.path.join(base_dir, "dados-conveniar")

# Testar para as 3 contas:
# Conta 376 (SEBRAE):
# Saldo anterior em 31/08: 1.621,27
# Conveniar 30/09: +321.37, -200.93
# Conveniar 20/10: +107.99, -95.15
# Saldo final da rubrica no Conveniar: 1.754,55
s_376 = 1621.27 + 321.37 - 200.93 + 107.99 - 95.15
print(f"Conta 376: Calculado={s_376:.2f} vs Conveniar=1754.55 (Dif={s_376 - 1754.55})")

# Conta 377 (EMBRAPII):
# Saldo anterior em 31/08: 2.151,97
# Conveniar 30/09: +784.16, -32.07
# Conveniar 20/10: +419.44, -303.97
# Saldo final da rubrica no Conveniar: 3.019,53
s_377 = 2151.97 + 784.16 - 32.07 + 419.44 - 303.97
print(f"Conta 377: Calculado={s_377:.2f} vs Conveniar=3019.53 (Dif={s_377 - 3019.53})")
