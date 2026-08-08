import 'package:flutter/material.dart';
import 'main_screen.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';

class LoginFlow extends StatefulWidget {
  const LoginFlow({super.key});

  @override
  State<LoginFlow> createState() => _LoginFlowState();
}

enum LoginStep { splash, start, phone, profile, preferences, finalStep }

class _LoginFlowState extends State<LoginFlow> {
  LoginStep _currentStep = LoginStep.splash;
  final ApiService _apiService = ApiService();
  late AuthService _authService;

  @override
  void initState() {
    super.initState();
    _authService = AuthService(_apiService);
    _checkLoginStatus();
    // Auto-advance splash screen after vehicle animations complete
    Future.delayed(const Duration(seconds: 9), () {
      if (mounted && _currentStep == LoginStep.splash) {
        setState(() => _currentStep = LoginStep.start);
      }
    });
  }

  Future<void> _checkLoginStatus() async {
    final isLoggedIn = await _authService.isLoggedIn();
    if (isLoggedIn && mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (context) => const MainScreen()),
      );
    }
  }

  void _nextStep(LoginStep step) {
    setState(() => _currentStep = step);
  }

  Future<void> _handleGoogleSignIn() async {
    try {
      await _authService.signInWithGoogle();
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (context) => const MainScreen()),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Google sign-in failed: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 300),
          transitionBuilder: (Widget child, Animation<double> animation) {
            return SlideTransition(
              position: Tween<Offset>(
                begin: const Offset(0.0, 0.2),
                end: Offset.zero,
              ).animate(CurvedAnimation(parent: animation, curve: Curves.easeOut)),
              child: FadeTransition(opacity: animation, child: child),
            );
          },
          child: _buildCurrentStep(),
        ),
      ),
    );
  }

  Widget _buildCurrentStep() {
    switch (_currentStep) {
      case LoginStep.splash:
        return SplashStep(key: const ValueKey('splash'));
      case LoginStep.start:
        return StartStep(
          key: const ValueKey('start'),
          onNext: () => _nextStep(LoginStep.phone),
          onGoogleSignIn: _handleGoogleSignIn,
        );
      case LoginStep.phone:
        return PhoneStep(
          key: const ValueKey('phone'),
          authService: _authService,
          onVerified: () => _nextStep(LoginStep.profile),
          onGoogleSignIn: _handleGoogleSignIn,
        );
      case LoginStep.profile:
        return ProfileStep(
          key: const ValueKey('profile'),
          authService: _authService,
          onNext: () => _nextStep(LoginStep.preferences),
        );
      case LoginStep.preferences:
        return PreferencesStep(
          key: const ValueKey('preferences'),
          onNext: () => _nextStep(LoginStep.finalStep),
        );
      case LoginStep.finalStep:
        return FinalStep(
          key: const ValueKey('finalStep'),
          onFinish: () async {
            // Mock login success - in real app, this would call actual auth
            // For now, we'll just navigate to main screen
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(builder: (context) => const MainScreen()),
            );
          },
        );
    }
  }
}

// ---------------------------------------------------------
// REUSABLE COMPONENTS
// ---------------------------------------------------------

class PrimaryButton extends StatelessWidget {
  final String text;
  final VoidCallback onPressed;
  
  const PrimaryButton({super.key, required this.text, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: Theme.of(context).colorScheme.primary,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
          elevation: 0,
        ),
        child: Text(text, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
      ),
    );
  }
}

class SecondaryButton extends StatelessWidget {
  final String text;
  final VoidCallback onPressed;
  
  const SecondaryButton({super.key, required this.text, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFFF4F6FB),
          foregroundColor: const Color(0xFF1A1B35),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
          elevation: 0,
        ),
        child: Text(text, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
      ),
    );
  }
}

// ---------------------------------------------------------
// STEPS
// ---------------------------------------------------------

class SplashStep extends StatefulWidget {
  const SplashStep({super.key});

  @override
  State<SplashStep> createState() => _SplashStepState();
}

class _SplashStepState extends State<SplashStep> with SingleTickerProviderStateMixin {
  late AnimationController _progressController;

  @override
  void initState() {
    super.initState();
    // Progress bar and vehicle position controller over 9 seconds
    _progressController = AnimationController(
      duration: const Duration(seconds: 9),
      vsync: this,
    );
    _progressController.forward();
  }

  @override
  void dispose() {
    _progressController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Spacer(flex: 3),
          // Logo (bigger!)
          Image.asset(
            'assets/images/logo.png',
            width: 260,
            fit: BoxFit.contain,
          ),
          const Spacer(flex: 2),
          // Vehicle and Progress Bar stacked
          SizedBox(
            width: 220,
            child: Column(
              children: [
                // Vehicle running track
                SizedBox(
                  height: 36,
                  child: AnimatedBuilder(
                    animation: _progressController,
                    builder: (context, child) {
                      final val = _progressController.value;
                      
                      // Determine image based on progress thirds
                      String imagePath;
                      bool isAuto = false;
                      if (val < 1.0 / 3.0) {
                        imagePath = 'assets/images/auto.png';
                        isAuto = true;
                      } else if (val < 2.0 / 3.0) {
                        imagePath = 'assets/images/train.png';
                      } else {
                        imagePath = 'assets/images/cab.png';
                      }

                      // Map progress (0.0 to 1.0) to Alignment X (-1.0 to 1.0)
                      final alignmentX = -1.0 + (val * 2.0);

                      Widget imageWidget = Image.asset(
                        imagePath,
                        width: 48,
                        height: 36,
                        fit: BoxFit.contain,
                        errorBuilder: (context, error, stackTrace) {
                          return Container(
                            width: 48,
                            height: 36,
                            color: Colors.grey.shade300,
                            alignment: Alignment.center,
                            child: Text(
                              val < 1.0 / 3.0 ? 'Auto' : (val < 2.0 / 3.0 ? 'Train' : 'Cab'),
                              style: const TextStyle(fontSize: 8, color: Colors.black, fontWeight: FontWeight.bold),
                            ),
                          );
                        },
                      );

                      // Flip the auto image horizontally to face forward (right)
                      if (isAuto) {
                        imageWidget = Transform.flip(
                          flipX: false,
                          child: imageWidget,
                        );
                      }

                      return Align(
                        alignment: Alignment(alignmentX, 0),
                        child: imageWidget,
                      );
                    },
                  ),
                ),
                // Loading Bar (run directly on top)
                ClipRRect(
                  borderRadius: BorderRadius.circular(99),
                  child: SizedBox(
                    height: 6,
                    child: AnimatedBuilder(
                      animation: _progressController,
                      builder: (context, child) {
                        return LinearProgressIndicator(
                          value: _progressController.value,
                          backgroundColor: const Color(0xFFF4F6FB),
                          color: Colors.black,
                        );
                      },
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // Tagline below loader
          RichText(
            text: const TextSpan(
              style: TextStyle(
                fontSize: 14,
                color: Colors.black,
                letterSpacing: 0.5,
              ),
              children: [
                TextSpan(text: 'multiple transit  ', style: TextStyle(fontWeight: FontWeight.normal)),
                TextSpan(text: 'one', style: TextStyle(fontWeight: FontWeight.bold)),
                TextSpan(text: ' app', style: TextStyle(fontWeight: FontWeight.normal)),
              ],
            ),
          ),
          const Spacer(flex: 3),
        ],
      ),
    );
  }
}

class StartStep extends StatelessWidget {
  final VoidCallback onNext;
  final VoidCallback? onGoogleSignIn;
  const StartStep({super.key, required this.onNext, this.onGoogleSignIn});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        children: [
          const SizedBox(height: 24),
          Expanded(
            child: Image.asset('assets/images/login_screen_image.png', fit: BoxFit.contain),
          ),
          const SizedBox(height: 32),
          const Text('Get started', style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Color(0xFF1A1B35))),
          const SizedBox(height: 8),
          const Text('Designed for seamless journeys ahead.\nBegin the way you prefer.', 
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 15, color: Color(0xFF8C90A3), height: 1.5),
          ),
          const SizedBox(height: 32),
          PrimaryButton(text: 'Continue with Phone', onPressed: onNext),
          const SizedBox(height: 12),
          SecondaryButton(text: 'Continue with Gmail', onPressed: onGoogleSignIn ?? onNext),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _buildIconButton(''),
              const SizedBox(width: 16),
              GestureDetector(onTap: onGoogleSignIn, child: _buildIconButton('G')),
            ],
          ),
          const SizedBox(height: 32),
          TextButton(
            onPressed: onNext,
            child: const Text('Already a user? Sign in', style: TextStyle(color: Color(0xFF5974FF), fontWeight: FontWeight.w600)),
          ),
          TextButton(
            onPressed: onNext,
            child: const Text('Skip Sign in', style: TextStyle(color: Color(0xFF5974FF), fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }

  Widget _buildIconButton(String symbol) {
    return Container(
      width: 56, height: 56,
      decoration: const BoxDecoration(color: Color(0xFFF4F6FB), shape: BoxShape.circle),
      alignment: Alignment.center,
      child: Text(symbol, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF1A1B35))),
    );
  }
}

class PhoneStep extends StatefulWidget {
  final AuthService authService;
  final VoidCallback onVerified;
  final VoidCallback? onGoogleSignIn;

  const PhoneStep({
    super.key,
    required this.authService,
    required this.onVerified,
    this.onGoogleSignIn,
  });

  @override
  State<PhoneStep> createState() => _PhoneStepState();
}

class _PhoneStepState extends State<PhoneStep> {
  final TextEditingController _phoneController = TextEditingController();
  final List<TextEditingController> _otpControllers = List.generate(6, (_) => TextEditingController());
  bool _otpSent = false;
  bool _isLoading = false;
  String? _statusMessage;

  @override
  void dispose() {
    _phoneController.dispose();
    for (final controller in _otpControllers) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _sendOtp() async {
    final phoneText = _phoneController.text.trim();
    if (phoneText.isEmpty) {
      setState(() => _statusMessage = 'Please enter your phone number.');
      return;
    }

    String phone = phoneText;
    if (!phone.startsWith('+')) {
      phone = '+91$phone';
    }

    setState(() {
      _isLoading = true;
      _statusMessage = null;
    });

    try {
      await widget.authService.requestPhoneOtp(phone);
      setState(() {
        _otpSent = true;
        _statusMessage = 'OTP sent to $phone. Enter it below.';
      });
    } catch (e) {
      setState(() {
        _statusMessage = 'Failed to send OTP: $e';
      });
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _verifyOtp() async {
    final otp = _otpControllers.map((controller) => controller.text.trim()).join();
    if (otp.length != 6) {
      setState(() => _statusMessage = 'Enter the 6-digit OTP.');
      return;
    }

    final phoneText = _phoneController.text.trim();
    String phone = phoneText;
    if (!phone.startsWith('+')) {
      phone = '+91$phone';
    }

    setState(() {
      _isLoading = true;
      _statusMessage = null;
    });

    try {
      await widget.authService.verifyPhoneOtp(phone, otp);
      widget.onVerified();
    } catch (e) {
      setState(() {
        _statusMessage = 'OTP verification failed: $e';
      });
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Center(child: Text('Secure Your Account', style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Color(0xFF1A1B35)))),
          const SizedBox(height: 40),
          const Text('Add Your Phone no.', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Color(0xFF1A1B35))),
          const SizedBox(height: 8),
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                decoration: BoxDecoration(color: const Color(0xFFF4F6FB), borderRadius: BorderRadius.circular(16)),
                child: const Text('+91', style: TextStyle(fontSize: 15)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: InputDecoration(
                    hintText: '000 000 0000',
                    filled: true,
                    fillColor: const Color(0xFFF4F6FB),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          if (_otpSent) ...[
            const Text('Enter Otp', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Color(0xFF1A1B35))),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: List.generate(6, (index) => _buildOtpBox(index)),
            ),
            const SizedBox(height: 16),
          ],
          if (_statusMessage != null) ...[
            Text(_statusMessage!, style: const TextStyle(color: Color(0xFF5974FF))),
            const SizedBox(height: 16),
          ],
          const Spacer(),
          PrimaryButton(
            text: _otpSent ? 'Confirm OTP' : 'Send OTP',
            onPressed: _isLoading ? () {} : (_otpSent ? _verifyOtp : _sendOtp),
          ),
          const SizedBox(height: 16),
          Center(
            child: TextButton(
              onPressed: widget.onGoogleSignIn,
              child: const Text('Continue with Google', style: TextStyle(color: Color(0xFF5974FF), fontWeight: FontWeight.w600)),
            ),
          )
        ],
      ),
    );
  }

  Widget _buildOtpBox(int index) {
    return Container(
      width: 50,
      height: 50,
      decoration: BoxDecoration(color: const Color(0xFFF4F6FB), borderRadius: BorderRadius.circular(12)),
      child: TextField(
        controller: _otpControllers[index],
        textAlign: TextAlign.center,
        keyboardType: TextInputType.number,
        maxLength: 1,
        style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        decoration: const InputDecoration(border: InputBorder.none, counterText: ''),
        onChanged: (value) {
          if (value.length == 1) {
            if (index + 1 < _otpControllers.length) {
              FocusScope.of(context).nextFocus();
            } else {
              FocusScope.of(context).unfocus();
            }
          }
        },
      ),
    );
  }
}

class ProfileStep extends StatefulWidget {
  final AuthService authService;
  final VoidCallback onNext;

  const ProfileStep({super.key, required this.authService, required this.onNext});

  @override
  State<ProfileStep> createState() => _ProfileStepState();
}

class _ProfileStepState extends State<ProfileStep> {
  final TextEditingController _nameController = TextEditingController();
  bool _isLoading = false;
  String? _statusMessage;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _loadProfile() async {
    try {
      final user = await widget.authService.getCurrentUser();
      _nameController.text = user.name ?? '';
    } catch (_) {
      setState(() {
        _statusMessage = 'Unable to load profile information right now.';
      });
    }
  }

  Future<void> _saveProfile() async {
    final name = _nameController.text.trim();
    if (name.isEmpty) {
      setState(() => _statusMessage = 'Please enter your name before continuing.');
      return;
    }

    setState(() {
      _isLoading = true;
      _statusMessage = null;
    });

    try {
      await widget.authService.updateProfileName(name);
      widget.onNext();
    } catch (e) {
      setState(() {
        _statusMessage = 'Unable to save profile: $e';
      });
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Center(child: Text('Create your Profile', style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Color(0xFF1A1B35)))),
          const SizedBox(height: 32),
          _buildInputLabel('Your Name'),
          TextField(
            controller: _nameController,
            decoration: InputDecoration(
              hintText: 'Enter your name',
              filled: true,
              fillColor: const Color(0xFFF4F6FB),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
              contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'This name will appear in your profile and help personalize your experience.',
            style: TextStyle(fontSize: 14, color: Color(0xFF8C90A3), height: 1.5),
          ),
          if (_statusMessage != null) ...[
            const SizedBox(height: 16),
            Text(_statusMessage!, style: const TextStyle(color: Color(0xFF5974FF))),
          ],
          const Spacer(),
          PrimaryButton(
            text: _isLoading ? 'Saving…' : 'Continue',
            onPressed: _isLoading ? () {} : _saveProfile,
          ),
        ],
      ),
    );
  }

  Widget _buildInputLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8, left: 4),
      child: Text(text, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Color(0xFF1A1B35))),
    );
  }
}

class PreferencesStep extends StatefulWidget {
  final VoidCallback onNext;
  const PreferencesStep({super.key, required this.onNext});

  @override
  State<PreferencesStep> createState() => _PreferencesStepState();
}

class _PreferencesStepState extends State<PreferencesStep> {
  final List<String> allPreferences = [
    'Solo Traveller', 'Group Traveller', 'Adventure', 'Explorer', 
    'Metro', 'Walking', 'Bus', 'Train', 'Fastest Route', 
    'Shortest Route', 'Carpool', 'Multimodal', 'Single Trips', 
    'Budget Trips', 'Comfort Trips'
  ];
  final Set<String> selectedPrefs = {};

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Center(child: Text('Select Travel Preferences', style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Color(0xFF1A1B35)))),
          const SizedBox(height: 32),
          Expanded(
            child: SingleChildScrollView(
              child: Wrap(
                spacing: 12, runSpacing: 12,
                children: allPreferences.map((pref) {
                  final isActive = selectedPrefs.contains(pref);
                  return GestureDetector(
                    onTap: () {
                      setState(() {
                        if (isActive) {
                          selectedPrefs.remove(pref);
                        } else {
                          selectedPrefs.add(pref);
                        }
                      });
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                      decoration: BoxDecoration(
                        color: isActive ? const Color(0xFFEBF0FF) : const Color(0xFFF4F6FB),
                        borderRadius: BorderRadius.circular(999),
                        border: Border.all(color: isActive ? const Color(0xFF5974FF) : Colors.transparent),
                      ),
                      child: Text(pref, style: TextStyle(
                        fontSize: 14, fontWeight: FontWeight.w600,
                        color: isActive ? const Color(0xFF5974FF) : const Color(0xFF8C90A3),
                      )),
                    ),
                  );
                }).toList(),
              ),
            ),
          ),
          PrimaryButton(text: 'Confirm', onPressed: widget.onNext),
        ],
      ),
    );
  }
}

class FinalStep extends StatelessWidget {
  final VoidCallback onFinish;
  const FinalStep({super.key, required this.onFinish});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        children: [
          const SizedBox(height: 40),
          Expanded(
            child: Image.asset('assets/images/login_screen_image.png', fit: BoxFit.contain),
          ),
          const SizedBox(height: 32),
          const Text('Find Your Way!', style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Color(0xFF1A1B35))),
          const Spacer(),
          PrimaryButton(text: 'Get Started!', onPressed: onFinish),
          const SizedBox(height: 16),
          RichText(
            textAlign: TextAlign.center,
            text: const TextSpan(
              style: TextStyle(fontSize: 12, color: Color(0xFF8C90A3), height: 1.5),
              children: [
                TextSpan(text: 'By using WAY Transit, you agree to the\n'),
                TextSpan(text: 'Terms', style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1A1B35))),
                TextSpan(text: ' and '),
                TextSpan(text: 'Privacy Policy.', style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1A1B35))),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
