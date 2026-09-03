import 'package:flutter/material.dart';

class TypingIndicator extends StatefulWidget {
  final Color color;

  const TypingIndicator({this.color = const Color(0xFF5974FF), super.key});

  @override
  State<TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<TypingIndicator> with TickerProviderStateMixin {
  late final List<AnimationController> _animationControllers;
  late final List<Animation<double>> _animations;

  @override
  void initState() {
    super.initState();
    _animationControllers = List.generate(
      3,
      (index) => AnimationController(duration: const Duration(milliseconds: 600), vsync: this),
    );

    _animations = _animationControllers.asMap().entries.map((entry) {
      final controller = entry.value;
      return Tween<double>(
        begin: 0,
        end: 8,
      ).animate(CurvedAnimation(parent: controller, curve: Curves.easeInOut));
    }).toList();

    for (int i = 0; i < _animationControllers.length; i++) {
      _animationControllers[i].repeat(
        reverse: true,
        period: Duration(milliseconds: 600 + (i * 100)),
      );
    }
  }

  @override
  void dispose() {
    for (var controller in _animationControllers) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildAIAvatar(),
          const SizedBox(width: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: const Color(0xFFF0F2F7),
              borderRadius: BorderRadius.circular(18),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.05),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: SizedBox(
              height: 20,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: List.generate(
                  3,
                  (index) => Padding(
                    padding: EdgeInsets.only(right: index < 2 ? 6 : 0),
                    child: AnimatedBuilder(
                      animation: _animations[index],
                      builder: (context, child) {
                        return Transform.translate(
                          offset: Offset(0, -_animations[index].value),
                          child: Container(
                            width: 8,
                            height: 8,
                            decoration: BoxDecoration(color: widget.color, shape: BoxShape.circle),
                          ),
                        );
                      },
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAIAvatar() {
    return Container(
      width: 32,
      height: 32,
      decoration: BoxDecoration(
        color: const Color(0xFF5974FF),
        borderRadius: BorderRadius.circular(8),
      ),
      child: const Center(child: Text('🤖', style: TextStyle(fontSize: 18))),
    );
  }
}
