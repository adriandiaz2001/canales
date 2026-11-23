# Crea la tarea de Windows "Publicador canales" que revisa la cola cada 10 minutos.
# Ejecútalo tú (una vez) cuando ya estén hechas las autorizaciones:
#   powershell -ExecutionPolicy Bypass -File C:\Proyectos\canal-faceless\publicador\instalar_tarea.ps1
# Para quitarla:  Unregister-ScheduledTask -TaskName "Publicador canales" -Confirm:$false

$python = (Get-Command python).Source
$accion = New-ScheduledTaskAction -Execute $python -Argument "-m publicador.publicar" -WorkingDirectory "C:\Proyectos\canal-faceless"
$disparador = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 10)
# StartWhenAvailable: si el PC estaba apagado, lo hace al encenderlo. WakeToRun: despierta el PC si está en suspensión.
$ajustes = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 50) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName "Publicador canales" -Action $accion -Trigger $disparador -Settings $ajustes -Description "Publica la cola de C:\Proyectos\canal-faceless\publicador\cola.json" -Force
Write-Host "Tarea creada. Registro en C:\Proyectos\canal-faceless\publicador\registro.log"
