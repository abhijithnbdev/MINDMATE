import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../../core/constants/api_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../widgets/stat_card.dart';

class DashboardScreen extends StatefulWidget {
  final String userId;
  const DashboardScreen({super.key, required this.userId});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic>? _data;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _fetchDashboard();
  }

  Future<void> _fetchDashboard() async {
    try {
      final response = await http.get(Uri.parse("${ApiConstants.dashboardEndpoint}?user_id=${widget.userId}"));
      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            _data = jsonDecode(response.body);
            _loading = false;
          });
        }
      }
    } catch (e) {
      print("Error fetching dashboard: $e");
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    // If loading, show spinner. If done but data is null (error), show defaults.
    if (_loading) {
      return const Center(child: CircularProgressIndicator(color: AppTheme.primaryMint));
    }

    // Safely extract data with defaults
    final topCat = _data?['top_category'] ?? "None";
    final eventCount = _data?['event_count'] ?? 0;
    final date = _data?['date'] ?? "Today";
    final timeline = _data?['timeline'] as List? ?? [];

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                children: [
                   CircleAvatar(radius: 20, backgroundColor: AppTheme.surface, child: Text(widget.userId[0].toUpperCase())),
                   const SizedBox(width: 12),
                   Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text("Good Day, ${widget.userId}", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      const Text("SYSTEM ONLINE", style: TextStyle(color: AppTheme.primaryMint, fontSize: 10, letterSpacing: 1))
                   ]),
                ],
              ),
              const SizedBox(height: 30),

              // Focus Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppTheme.surface,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: Colors.white.withOpacity(0.05)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text("TODAY'S TOP CATEGORY", style: TextStyle(color: AppTheme.primaryMint.withOpacity(0.8), fontSize: 12)),
                    const SizedBox(height: 10),
                    Text(topCat.toString().toUpperCase(), style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: Colors.white)),
                    const SizedBox(height: 10),
                    Text("You have $eventCount events logged for $date.", style: const TextStyle(color: AppTheme.textSecondary)),
                  ],
                ),
              ),

              const SizedBox(height: 30),
              
              // Stats Grid
              GridView.count(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisCount: 2,
                crossAxisSpacing: 15,
                mainAxisSpacing: 15,
                childAspectRatio: 1.4,
                children: [
                  DashboardStatCard(label: "Events", value: "$eventCount", icon: Icons.calendar_today),
                  const DashboardStatCard(label: "System", value: "Optimal", icon: Icons.check_circle_outline),
                ],
              ),

              const SizedBox(height: 30),
              
              // Timeline Section (Optional Visual)
              if (timeline.isNotEmpty) ...[
                const Text("TIMELINE", style: TextStyle(color: Colors.grey, letterSpacing: 1.5)),
                const SizedBox(height: 10),
                ...timeline.map((item) => Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  padding: const EdgeInsets.all(15),
                  decoration: BoxDecoration(
                    color: const Color(0xFF252525),
                    borderRadius: BorderRadius.circular(10),
                    border: Border(left: BorderSide(color: Colors.teal.shade200, width: 4)),
                  ),
                  child: Text(item.toString(), style: const TextStyle(color: Colors.white)),
                )).toList(),
              ]
            ],
          ),
        ),
      ),
    );
  }
}
