import 'package:flutter/material.dart';
import 'home_screen.dart';
import 'profile_screen.dart';
import 'wallet_screen.dart';
import 'add_ticket_screen.dart';
import 'ride_search_screen.dart';
import 'ai_chat/ai_chat_screen.dart';
import '../nav/app_nav.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    HomeScreen(),
    RideSearchScreen(),
    ProfileScreen(),
    AddTicketScreen(),
    WalletScreen(),
  ];

  @override
  void initState() {
    super.initState();
    AppNav.tabIndex.addListener(_onTabChanged);
  }

  @override
  void dispose() {
    AppNav.tabIndex.removeListener(_onTabChanged);
    super.dispose();
  }

  void _onTabChanged() {
    final next = AppNav.tabIndex.value;
    if (next != _currentIndex && mounted) {
      setState(() => _currentIndex = next);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: _screens),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() => _currentIndex = index);
          AppNav.tabIndex.value = index;
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(
            icon: Icon(Icons.directions_car),
            label: 'Rides',
          ),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
          BottomNavigationBarItem(
            icon: Icon(Icons.add_circle),
            label: 'Add Ticket',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.account_balance_wallet),
            label: 'Wallet',
          ),
        ],
        type: BottomNavigationBarType.fixed,
        selectedItemColor: const Color(0xFF5974FF),
        unselectedItemColor: const Color(0xFF8C90A3),
        backgroundColor: Colors.white,
        elevation: 8,
      ),
    );
  }
}
