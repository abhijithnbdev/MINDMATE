import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'features/dashboard/screens/dashboard_screen.dart';
import 'features/chat/screens/home_orb_screen.dart';
import 'features/memory/screens/memory_screen.dart';
import 'features/calendar/screens/calendar_screen.dart';
import 'features/settings/settings_screen.dart';

class MainLayout extends StatefulWidget {
  final String userId; 
  const MainLayout({super.key, required this.userId});

  @override
  State<MainLayout> createState() => _MainLayoutState();
}

class _MainLayoutState extends State<MainLayout> {
  int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    // Pass userId to the screens
    final List<Widget> screens = [
      DashboardScreen(userId: widget.userId),
      const CalendarScreen(),
      HomeOrbScreen(userId: widget.userId),
      const MemoryScreen(),
      const SettingsScreen(), 
    ];

    return Scaffold(
      body: screens[_selectedIndex],
      bottomNavigationBar: Container(
        margin: const EdgeInsets.all(20),
        height: 70,
        decoration: BoxDecoration(
          color: AppTheme.surface.withOpacity(0.9),
          borderRadius: BorderRadius.circular(25),
          border: Border.all(color: Colors.white.withOpacity(0.1)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.3),
              blurRadius: 10,
              offset: const Offset(0, 5),
            ),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildNavItem(Icons.grid_view_rounded, 0),
            _buildNavItem(Icons.calendar_today_rounded, 1),
            
            // The Glowing AI Button
            GestureDetector(
              onTap: () => setState(() => _selectedIndex = 2),
              child: Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: AppTheme.primaryMint,
                  shape: BoxShape.circle,
                  boxShadow: [AppTheme.glowBoxShadow],
                ),
                child: const Icon(Icons.smart_toy_rounded, color: Colors.black, size: 30),
              ),
            ),
            
            _buildNavItem(Icons.search_rounded, 3),
            _buildNavItem(Icons.settings_rounded, 4),
          ],
        ),
      ),
      extendBody: true,
    );
  }

  Widget _buildNavItem(IconData icon, int index) {
    final isSelected = _selectedIndex == index;
    return IconButton(
      icon: Icon(
        icon,
        color: isSelected ? AppTheme.primaryMint : AppTheme.textSecondary,
        size: 28,
      ),
      onPressed: () => setState(() => _selectedIndex = index),
    );
  }
}
