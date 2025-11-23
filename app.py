@app.get("/config")
def config():
    html = """<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8" />
  <title>CyberAware – Configuração</title>
</head>
<body>
  <h2>Configuração da atividade CyberAware</h2>

  <label>Duração (minutos):
    <input type="number" name="duracao" value="15" />
  </label>
  <br/><br/>

  <label>Nível de dificuldade:
    <select name="dificuldade">
      <option value="easy">Fácil</option>
      <option value="medium" selected>Médio</option>
      <option value="hard">Difícil</option>
    </select>
  </label>
  <br/><br/>

  <label>Instruções para o aluno:<br/>
    <textarea name="instrucoes" rows="4" cols="50">Introdução à atividade CyberAware.</textarea>
  </label>
</body>
</html>"""
    return html

