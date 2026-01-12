import 'package:flutter/material.dart';
import 'package:flutter_web_plugins/url_strategy.dart'; // Add url_strategy package later if needed
import 'routes/app_router.dart';
import 'core/theme/vanguard_theme.dart';

void main() {
  // Ensure that plugin services are initialized
  WidgetsFlutterBinding.ensureInitialized();
  
  // Use PathUrlStrategy for web (remove /#/)
  usePathUrlStrategy();

  runApp(const VanguardApp());
}

class VanguardApp extends StatelessWidget {
  const VanguardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Vanguard | Sports Arbitrage',
      debugShowCheckedModeBanner: false,
      
      // Theme Configuration
      theme: VanguardTheme.darkTheme,
      themeMode: ThemeMode.dark, // Enforce Dark Mode for "Cyber-Dark" vibe

      // Routing
      routerConfig: AppRouter.router,
    );
  }
}
