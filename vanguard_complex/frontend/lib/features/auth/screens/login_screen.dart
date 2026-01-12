import 'package:flutter/material.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _handleLogin() {
    if (_formKey.currentState?.validate() ?? false) {
      // TODO: Implement Auth Logic connecting to FastAPI
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Conectando ao Vanguard Core...')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 400),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Logo / Header
                  const Icon(
                    Icons.bolt,
                    size: 64,
                    color: Color(0xFF8B5CF6), // Primary
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'VANGUARD',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.w900,
                          letterSpacing: 2.0,
                        ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Intelligence Core Access',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Colors.white54,
                        ),
                  ),
                  
                  const SizedBox(height: 48),

                  // Inputs
                  TextFormField(
                    controller: _emailController,
                    decoration: const InputDecoration(
                      labelText: 'ID Operacional (Email)',
                      prefixIcon: Icon(Icons.person_outline),
                    ),
                    keyboardType: TextInputType.emailAddress,
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'ID obrigatório';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _passwordController,
                    decoration: const InputDecoration(
                      labelText: 'Chave de Acesso (Senha)',
                      prefixIcon: Icon(Icons.lock_outline),
                    ),
                    obscureText: true,
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'Chave obrigatória';
                      }
                      return null;
                    },
                  ),

                  const SizedBox(height: 32),

                  // Action
                  ElevatedButton(
                    onPressed: _handleLogin,
                    child: const Text('INICIAR SESSÃO'),
                  ),

                  const SizedBox(height: 24),
                  
                  // Compliance Footer
                  const Text(
                    'Acesso restrito a pessoal autorizado. Todas as ações são monitoradas e auditadas conforme Lei 14.790.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 10, color: Colors.white24),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
