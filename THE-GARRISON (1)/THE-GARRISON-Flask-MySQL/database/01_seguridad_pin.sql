-- Ejecutar una sola vez sobre la base ya importada.
-- login.php convierte los PIN de texto a hashes al primer inicio de sesión correcto.
ALTER TABLE empleados
    ADD COLUMN pin_hash VARCHAR(255) NULL AFTER pin,
    MODIFY COLUMN pin VARCHAR(20) NULL;
