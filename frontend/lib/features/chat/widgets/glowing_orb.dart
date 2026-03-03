import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

class GlowingOrb extends StatefulWidget {
  final bool isListening;
  final double size;
  const GlowingOrb({super.key, required this.isListening, this.size = 280});

  @override
  State<GlowingOrb> createState() => _GlowingOrbState();
}

class _GlowingOrbState extends State<GlowingOrb> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 4),
    );
    if (widget.isListening) {
      _controller.repeat(reverse: true);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant GlowingOrb oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isListening && !_controller.isAnimating) {
      _controller.repeat(reverse: true);
    } else if (!widget.isListening && _controller.isAnimating) {
      _controller.stop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Container(
          width: widget.size,
          height: widget.size,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            // The Gradient
            gradient: const LinearGradient(
              colors: [
                Color(0xFF2C3E50),
                Color(0xFF00DC82), // Mint
                Color(0xFF00F0FF), // Cyan
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            // The Glow
            boxShadow: [
              BoxShadow(
                color: AppTheme.primaryMint.withOpacity(0.3),
                blurRadius: widget.isListening ? 40 + 10 * _controller.value : 30,
                spreadRadius: widget.isListening ? 10 + 15 * _controller.value : 8,
              )
            ],
          ),
          child: Container(
             // Inner shadow overlay for depth
             decoration: BoxDecoration(
               shape: BoxShape.circle,
               gradient: RadialGradient(
                 colors: [
                   Colors.transparent,
                   Colors.black.withOpacity(0.3),
                 ],
               ),
             ),
          ),
        );
      },
    );
  }
}
