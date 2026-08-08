import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../models/user.dart';
import 'login_flow.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final ApiService _apiService = ApiService();
  late final AuthService _authService;
  late Future<User> _userFuture;
  final TextEditingController _nameController = TextEditingController();
  bool _isSaving = false;
  String? _statusMessage;

  @override
  void initState() {
    super.initState();
    _authService = AuthService(_apiService);
    _userFuture = _loadUser();
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<User> _loadUser() async {
    final user = await _authService.getCurrentUser();
    _nameController.text = user.name ?? '';
    return user;
  }

  void _refreshUser() {
    setState(() {
      _userFuture = _loadUser();
      _statusMessage = null;
    });
  }

  Future<void> _saveName() async {
    final name = _nameController.text.trim();
    if (name.isEmpty) {
      setState(() => _statusMessage = 'Please enter your name.');
      return;
    }

    setState(() {
      _isSaving = true;
      _statusMessage = null;
    });

    try {
      await _authService.updateProfileName(name);
      _refreshUser();
      setState(() => _statusMessage = 'Profile updated successfully.');
    } catch (e) {
      setState(() => _statusMessage = 'Failed to update profile: $e');
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }

  Future<void> _logout() async {
    await _authService.logout();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (context) => const LoginFlow()),
      (route) => false,
    );
  }

  Future<void> _deleteAccount() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Delete account'),
          content: const Text('This will permanently delete your account. Continue?'),
          actions: [
            TextButton(onPressed: () => Navigator.of(context).pop(false), child: const Text('Cancel')),
            TextButton(onPressed: () => Navigator.of(context).pop(true), child: const Text('Delete', style: TextStyle(color: Colors.red))),
          ],
        );
      },
    );

    if (confirm != true) return;

    try {
      await _authService.deleteAccount();
      if (!mounted) return;
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (context) => const LoginFlow()),
        (route) => false,
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to delete account: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<User>(
      future: _userFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            backgroundColor: Color(0xFFF8F9FE),
            body: Center(child: CircularProgressIndicator()),
          );
        }

        if (snapshot.hasError) {
          return Scaffold(
            backgroundColor: const Color(0xFFF8F9FE),
            body: Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text('Unable to load profile.', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 16),
                    Text(snapshot.error.toString(), textAlign: TextAlign.center),
                    const SizedBox(height: 24),
                    ElevatedButton(onPressed: _refreshUser, child: const Text('Retry')),
                  ],
                ),
              ),
            ),
          );
        }

        final user = snapshot.data!;
        final title = user.name ?? user.email ?? user.phone ?? 'WAY Rider';
        final subtitle = user.email ?? user.phone ?? 'Traveler';

        return Scaffold(
          backgroundColor: const Color(0xFFF8F9FE),
          body: SafeArea(
            child: SingleChildScrollView(
              child: Column(
                children: [
                  _buildProfileHeader(title, subtitle, user),
                  const SizedBox(height: 24),
                  _buildProfileCards(),
                  const SizedBox(height: 24),
                  _buildEditSection(user),
                  const SizedBox(height: 16),
                  if (_statusMessage != null)
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 20.0),
                      child: Text(_statusMessage!, style: const TextStyle(color: Color(0xFF5974FF))),
                    ),
                  const SizedBox(height: 24),
                  _buildBottomActions(),
                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildProfileHeader(String title, String subtitle, User user) {
    return Padding(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              color: const Color(0xFFF4F6FB),
              borderRadius: BorderRadius.circular(40),
            ),
            child: const Center(
              child: Text('👤', style: TextStyle(fontSize: 40)),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            title,
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Color(0xFF1A1B35),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            subtitle,
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Provider: ${user.authProvider ?? 'local'}',
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey[500],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProfileCards() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0),
      child: Row(
        children: [
          Expanded(child: _buildQuickCard('Documents ↗')),
          const SizedBox(width: 12),
          Expanded(child: _buildQuickCard('Help ↗')),
          const SizedBox(width: 12),
          Expanded(child: _buildQuickCard('FAQ ↗')),
        ],
      ),
    );
  }

  Widget _buildQuickCard(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Center(
        child: Text(
          text,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: Color(0xFF1A1B35),
          ),
        ),
      ),
    );
  }

  Widget _buildEditSection(User user) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Edit Profile', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF1A1B35))),
          const SizedBox(height: 16),
          TextField(
            controller: _nameController,
            decoration: InputDecoration(
              labelText: 'Name',
              filled: true,
              fillColor: const Color(0xFFF4F6FB),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
            ),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _isSaving ? null : _saveName,
            style: ElevatedButton.styleFrom(
              minimumSize: const Size.fromHeight(56),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            ),
            child: Text(_isSaving ? 'Saving...' : 'Save Profile'),
          ),
          const SizedBox(height: 20),
          Text('Account details', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Colors.grey[700])),
          const SizedBox(height: 12),
          _buildAccountDetail('Email', user.email ?? 'Not provided'),
          const SizedBox(height: 8),
          _buildAccountDetail('Phone', user.phone ?? 'Not provided'),
          const SizedBox(height: 8),
          _buildAccountDetail('Verified', user.isVerified ? 'Yes' : 'No'),
        ],
      ),
    );
  }

  Widget _buildAccountDetail(String label, String value) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE8EAEE)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF1A1B35))),
          Text(value, style: const TextStyle(color: Color(0xFF8C90A3))),
        ],
      ),
    );
  }

  Widget _buildBottomActions() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0),
      child: Column(
        children: [
          _buildMenuButton('Logout', Colors.white, _logout),
          const SizedBox(height: 12),
          _buildMenuButton('Delete Account', const Color(0xFFFFE5E5), _deleteAccount, textColor: const Color(0xFFFF4444)),
        ],
      ),
    );
  }

  Widget _buildMenuButton(String text, Color bgColor, VoidCallback onPressed, {Color? textColor}) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: bgColor,
          foregroundColor: textColor ?? const Color(0xFF1A1B35),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          elevation: 0,
          padding: const EdgeInsets.symmetric(vertical: 16),
        ),
        child: Text(
          text,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: textColor ?? const Color(0xFF1A1B35),
          ),
        ),
      ),
    );
  }
}
