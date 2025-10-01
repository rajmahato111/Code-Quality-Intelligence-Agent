"""Interactive Q&A shell for the Code Quality Intelligence Agent."""

import sys
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

try:
    import readline
    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Prompt

from ..rag.qa_engine import QAEngine, create_qa_engine
from ..rag.vector_store import VectorStoreManager
from ..llm.llm_service import create_llm_service
from ..core.models import AnalysisResult


logger = logging.getLogger(__name__)
console = Console()


class InteractiveQAShell:
    """Interactive shell for Q&A about analyzed codebase."""
    
    def __init__(self, analysis_result: AnalysisResult):
        """
        Initialize interactive Q&A shell.
        
        Args:
            analysis_result: Analysis result to create Q&A session for
        """
        self.analysis_result = analysis_result
        self.conversation_id: Optional[str] = None
        self.qa_engine: Optional[QAEngine] = None
        self.commands = {
            'help': self._cmd_help,
            'exit': self._cmd_exit,
            'quit': self._cmd_exit,
            'clear': self._cmd_clear,
            'history': self._cmd_history,
            'focus': self._cmd_focus,
            'navigate': self._cmd_navigate,
            'back': self._cmd_back,
            'summary': self._cmd_summary,
            'stats': self._cmd_stats,
            'suggestions': self._cmd_suggestions,
        }
        self.running = False
        
        # Set up command history
        self.history_file = Path.home() / '.codeql_history'
        self._setup_readline()
        
        # Initialize Q&A engine
        self._initialize_qa_engine()
    
    def _setup_readline(self) -> None:
        """Set up readline for command history and auto-completion."""
        if not READLINE_AVAILABLE:
            console.print("[yellow]Warning: readline not available. Command history and auto-completion disabled.[/yellow]")
            return
        
        try:
            # Load command history
            if self.history_file.exists():
                readline.read_history_file(str(self.history_file))
            
            # Set history length
            readline.set_history_length(1000)
            
            # Set up auto-completion
            readline.set_completer(self._completer)
            readline.parse_and_bind('tab: complete')
            
            # Enable history search
            readline.parse_and_bind('"\\e[A": history-search-backward')
            readline.parse_and_bind('"\\e[B": history-search-forward')
            
        except Exception as e:
            logger.debug(f"Failed to set up readline: {e}")
    
    def _save_history(self) -> None:
        """Save command history to file."""
        if not READLINE_AVAILABLE:
            return
        
        try:
            readline.write_history_file(str(self.history_file))
        except Exception as e:
            logger.debug(f"Failed to save history: {e}")
    
    def _completer(self, text: str, state: int) -> Optional[str]:
        """Auto-completion function for readline."""
        if state == 0:
            # Generate completion options
            self.completion_matches = []
            
            # Command completion
            if text.startswith('/'):
                command_text = text[1:]
                for cmd in self.commands.keys():
                    if cmd.startswith(command_text):
                        self.completion_matches.append(f'/{cmd}')
            else:
                # Question completion - suggest common question starters
                question_starters = [
                    "What is", "How does", "Where is", "Why does", "Can you explain",
                    "Show me", "Find", "List", "What are the", "How many"
                ]
                for starter in question_starters:
                    if starter.lower().startswith(text.lower()):
                        self.completion_matches.append(starter)
        
        try:
            return self.completion_matches[state]
        except IndexError:
            return None
    
    def _initialize_qa_engine(self) -> None:
        """Initialize the Q&A engine with the analysis result."""
        try:
            console.print("[blue]Initializing Q&A engine...[/blue]")
            
            # Create vector store and LLM service
            vector_store = VectorStoreManager()
            
            # Use OpenAI if API key is available, otherwise fall back to mock
            import os
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                llm_service = create_llm_service(provider="openai", api_key=openai_key)
            else:
                llm_service = create_llm_service(provider="mock")
            
            # Create Q&A engine
            self.qa_engine = create_qa_engine(vector_store, llm_service)
            
            # Index the codebase
            self.conversation_id = self.qa_engine.index_codebase(self.analysis_result)
            
            console.print("[green]✅ Q&A engine initialized successfully![/green]")
            
        except Exception as e:
            console.print(f"[red]❌ Failed to initialize Q&A engine: {e}[/red]")
            logger.error(f"Q&A engine initialization failed: {e}")
            raise
    
    def start(self) -> None:
        """Start the interactive Q&A shell."""
        self.running = True
        
        # Display welcome message
        self._display_welcome()
        
        try:
            while self.running:
                try:
                    # Get user input
                    user_input = self._get_user_input()
                    
                    if not user_input.strip():
                        continue
                    
                    # Process input
                    self._process_input(user_input)
                    
                except KeyboardInterrupt:
                    console.print("\n[yellow]Use /exit or /quit to leave the Q&A session.[/yellow]")
                    continue
                except EOFError:
                    break
        
        finally:
            self._save_history()
            console.print("\n[blue]Thanks for using the Code Quality Intelligence Agent![/blue]")
    
    def _display_welcome(self) -> None:
        """Display welcome message and instructions."""
        # Use smart score priority: maintainability_index if overall_score is 0
        display_score = self.analysis_result.metrics.overall_score
        if display_score <= 0 and hasattr(self.analysis_result.metrics, 'maintainability_index'):
            display_score = self.analysis_result.metrics.maintainability_index
        
        welcome_text = f"""
[bold blue]🤖 Interactive Q&A Mode[/bold blue]

Welcome to the interactive Q&A session for your codebase!

[bold]Codebase:[/bold] {self.analysis_result.codebase_path}
[bold]Files Analyzed:[/bold] {len(self.analysis_result.parsed_files)}
[bold]Issues Found:[/bold] {len(self.analysis_result.issues)}
[bold]Quality Score:[/bold] {round(display_score)}/100

[bold green]How to use:[/bold green]
• Ask natural language questions about your code
• Use /help to see available commands
• Use /exit or /quit to leave
• Press Tab for auto-completion
• Use arrow keys for command history

[bold yellow]Example questions:[/bold yellow]
• "What security issues were found?"
• "Show me the most complex functions"
• "What files have the most problems?"
• "How can I improve the code quality?"
"""
        
        console.print(Panel(welcome_text, title="Welcome", border_style="blue"))
    
    def _get_user_input(self) -> str:
        """Get user input with prompt."""
        try:
            # Show current focus if available
            focus_info = ""
            if self.qa_engine and self.conversation_id:
                current_focus = self.qa_engine.get_current_focus(self.conversation_id)
                if current_focus:
                    focus_info = f" [{current_focus.context_type}: {Path(current_focus.file_path).name}]"
            
            prompt_text = f"[bold blue]Q&A{focus_info}>[/bold blue] "
            return Prompt.ask(prompt_text, console=console)
            
        except Exception as e:
            logger.debug(f"Error getting user input: {e}")
            return ""
    
    def _process_input(self, user_input: str) -> None:
        """Process user input (command or question)."""
        user_input = user_input.strip()
        
        # Check if it's a command
        if user_input.startswith('/'):
            command = user_input[1:].split()[0].lower()
            args = user_input[1:].split()[1:] if len(user_input[1:].split()) > 1 else []
            
            if command in self.commands:
                self.commands[command](args)
            else:
                console.print(f"[red]Unknown command: /{command}[/red]")
                console.print("Use [bold]/help[/bold] to see available commands.")
        else:
            # It's a question
            self._handle_question(user_input)
    
    def _handle_question(self, question: str) -> None:
        """Handle a user question."""
        if not self.qa_engine or not self.conversation_id:
            console.print("[red]❌ Q&A engine not available[/red]")
            return
        
        try:
            console.print(f"[dim]Thinking...[/dim]")
            
            # Ask the question
            answer, confidence = self.qa_engine.ask_question(question, self.conversation_id)
            
            # Display the answer (hide confidence from output)
            self._display_answer(question, answer)
            
        except Exception as e:
            console.print(f"[red]❌ Error processing question: {e}[/red]")
            logger.error(f"Question processing failed: {e}")
    
    def _display_answer(self, question: str, answer: str) -> None:
        """Display the Q&A answer with formatting (confidence hidden)."""
        # Create question section with Rich markup
        question_section = Text()
        question_section.append("Question: ", style="bold")
        question_section.append(question)
        
        # Create the answer content with proper markdown rendering
        console.print(Panel(question_section, title="🤖 AI Assistant", border_style="green"))
        console.print("\n[bold]Answer:[/bold]")
        
        # Render the answer as markdown for proper formatting
        try:
            markdown_answer = Markdown(answer)
            console.print(markdown_answer)
        except Exception as e:
            # Fallback to plain text if markdown parsing fails
            console.print(answer)
            logger.debug(f"Markdown rendering failed: {e}")
        
        # Confidence intentionally hidden in CLI output
    
    def _show_suggestions(self) -> None:
        """Show suggestions for better questions."""
        suggestions = [
            "Try being more specific about files or functions",
            "Ask about specific quality categories (security, performance, etc.)",
            "Use /focus to navigate to specific code locations",
            "Ask about metrics or statistics with /stats"
        ]
        
        console.print("\n[yellow]💡 Try these suggestions for better results:[/yellow]")
        for suggestion in suggestions:
            console.print(f"  • {suggestion}")
        console.print()
    
    # Command implementations
    def _cmd_help(self, args: List[str]) -> None:
        """Show help information."""
        help_table = Table(title="Available Commands", show_header=True, header_style="bold magenta")
        help_table.add_column("Command", style="cyan", no_wrap=True)
        help_table.add_column("Description", style="white")
        
        commands_help = {
            "/help": "Show this help message",
            "/exit, /quit": "Exit the Q&A session",
            "/clear": "Clear the screen",
            "/history": "Show conversation history",
            "/focus <file>": "Focus on a specific file or function",
            "/navigate <location>": "Navigate to a code location",
            "/back": "Go back to previous focus location",
            "/summary": "Show conversation summary",
            "/stats": "Show Q&A session statistics",
            "/suggestions": "Get suggestions for related code"
        }
        
        for cmd, desc in commands_help.items():
            help_table.add_row(cmd, desc)
        
        console.print(help_table)
        
        console.print("\n[bold yellow]Example Questions:[/bold yellow]")
        examples = [
            "What security vulnerabilities were found?",
            "Show me the most complex functions",
            "Which files have the most issues?",
            "How can I improve performance?",
            "What are the main quality problems?",
            "Explain the issues in main.py"
        ]
        
        for example in examples:
            console.print(f"  • [green]{example}[/green]")
    
    def _cmd_exit(self, args: List[str]) -> None:
        """Exit the Q&A session."""
        console.print("[blue]Goodbye! 👋[/blue]")
        self.running = False
    
    def _cmd_clear(self, args: List[str]) -> None:
        """Clear the screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
        self._display_welcome()
    
    def _cmd_history(self, args: List[str]) -> None:
        """Show conversation history."""
        if not self.qa_engine or not self.conversation_id:
            console.print("[red]No conversation history available[/red]")
            return
        
        history = self.qa_engine.get_conversation_history(self.conversation_id)
        
        if not history:
            console.print("[yellow]No questions asked yet[/yellow]")
            return
        
        console.print(Panel("[bold]Conversation History[/bold]", border_style="blue"))
        
        for i, qa in enumerate(history[-10:], 1):  # Show last 10
            console.print(f"\n[bold cyan]{i}. Q:[/bold cyan] {qa.question}")
            console.print(f"[bold green]   A:[/bold green] {qa.answer[:100]}{'...' if len(qa.answer) > 100 else ''}")
            console.print(f"[dim]   Confidence: {qa.confidence:.1%} | Type: {qa.question_type.value}[/dim]")
    
    def _cmd_focus(self, args: List[str]) -> None:
        """Focus on a specific file or function."""
        if not args:
            # Show current focus
            if self.qa_engine and self.conversation_id:
                current_focus = self.qa_engine.get_current_focus(self.conversation_id)
                if current_focus:
                    console.print(f"[blue]Current focus: {current_focus}[/blue]")
                else:
                    console.print("[yellow]No current focus set[/yellow]")
            return
        
        target = " ".join(args)
        
        # Try to navigate to the target
        if self.qa_engine and self.conversation_id:
            # Simple file navigation
            success = self.qa_engine.navigate_to_code(self.conversation_id, target)
            if success:
                console.print(f"[green]✅ Focused on: {target}[/green]")
            else:
                console.print(f"[red]❌ Could not focus on: {target}[/red]")
    
    def _cmd_navigate(self, args: List[str]) -> None:
        """Navigate to a code location."""
        if not args:
            console.print("[yellow]Usage: /navigate <file_path> [function_name] [class_name][/yellow]")
            return
        
        file_path = args[0]
        function_name = args[1] if len(args) > 1 else None
        class_name = args[2] if len(args) > 2 else None
        
        if self.qa_engine and self.conversation_id:
            success = self.qa_engine.navigate_to_code(
                self.conversation_id, file_path, function_name, class_name
            )
            if success:
                console.print(f"[green]✅ Navigated to: {file_path}[/green]")
            else:
                console.print(f"[red]❌ Could not navigate to: {file_path}[/red]")
    
    def _cmd_back(self, args: List[str]) -> None:
        """Go back to previous focus location."""
        if self.qa_engine and self.conversation_id:
            success = self.qa_engine.navigate_back(self.conversation_id)
            if success:
                current_focus = self.qa_engine.get_current_focus(self.conversation_id)
                console.print(f"[green]✅ Navigated back to: {current_focus}[/green]")
            else:
                console.print("[yellow]No previous location to go back to[/yellow]")
    
    def _cmd_summary(self, args: List[str]) -> None:
        """Show conversation summary."""
        if not self.qa_engine or not self.conversation_id:
            console.print("[red]No conversation available[/red]")
            return
        
        summary = self.qa_engine.get_conversation_context_summary(self.conversation_id)
        if summary:
            console.print(Panel(summary, title="Conversation Summary", border_style="blue"))
        else:
            console.print("[yellow]No conversation summary available[/yellow]")
    
    def _cmd_stats(self, args: List[str]) -> None:
        """Show Q&A session statistics."""
        if not self.qa_engine:
            console.print("[red]No statistics available[/red]")
            return
        
        stats = self.qa_engine.get_statistics()
        
        stats_table = Table(title="Q&A Session Statistics", show_header=True, header_style="bold magenta")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Active Conversations", str(stats.get("active_conversations", 0)))
        stats_table.add_row("Total Questions", str(stats.get("total_questions", 0)))
        stats_table.add_row("Average Confidence", f"{stats.get('average_confidence', 0):.1%}")
        stats_table.add_row("Focus Changes", str(stats.get("total_focus_changes", 0)))
        
        console.print(stats_table)
        
        # Show question types breakdown
        question_types = stats.get("question_types", {})
        if question_types:
            console.print("\n[bold]Question Types:[/bold]")
            for qtype, count in question_types.items():
                console.print(f"  • {qtype.title()}: {count}")
    
    def _cmd_suggestions(self, args: List[str]) -> None:
        """Get suggestions for related code."""
        if not self.qa_engine or not self.conversation_id:
            console.print("[red]No suggestions available[/red]")
            return
        
        suggestions = self.qa_engine.suggest_related_code(self.conversation_id)
        
        if suggestions:
            console.print("[bold blue]🔍 Related Code Suggestions:[/bold blue]")
            for i, suggestion in enumerate(suggestions, 1):
                console.print(f"  {i}. [cyan]{suggestion}[/cyan]")
            console.print("\n[dim]Use /navigate <location> to jump to any of these locations[/dim]")
        else:
            console.print("[yellow]No related code suggestions available[/yellow]")


def start_interactive_qa(analysis_result: AnalysisResult) -> None:
    """
    Start an interactive Q&A session for the given analysis result.
    
    Args:
        analysis_result: Analysis result to create Q&A session for
    """
    try:
        shell = InteractiveQAShell(analysis_result)
        shell.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Q&A session interrupted[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Failed to start Q&A session: {e}[/red]")
        logger.error(f"Interactive Q&A failed: {e}")
        raise