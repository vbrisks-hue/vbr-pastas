import drive
s = drive.conectar()
for f in drive.listar_filhos(s, "root", so_pastas=True):
    print(ascii(f["name"]))
